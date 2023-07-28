import gspread
import requests
import csv
import json
import re
import os
from google.oauth2 import service_account
from typing import Union, Dict, List, Optional
from enum import Enum

from config import GSPREAD_SCOPE, GSHEET_CREDENTIALS_PATH, URL_FOR_GSHEET, \
    SPELLS_SHEET_NAME, CLASS_SHEET_NAME, RACES_SHEET_NAME, FEATURES_SHEET_NAME, TRAITS_SHEET_NAME, SKILLS_SHEET_NAME


class ParserToGsheet:
    def __init__(self, sheet_url = URL_FOR_GSHEET, scopes = GSPREAD_SCOPE, cred_path = GSHEET_CREDENTIALS_PATH, auth=None):
        self.sheet = gspread.authorize(
            service_account.Credentials.from_service_account_file(cred_path)
            .with_scopes(scopes)
        ).open_by_url(sheet_url)
        self.url = 'https://www.dnd5eapi.co/api/'
        self.auth = auth

    def _request(self, method: str = 'GET',
                 json_payload: Union[Dict, List, None] = None,
                 params: Optional[Dict] = None,
                 path: str = '', headers: Optional[Dict] = None
                 ) -> requests.Response:
        if headers is None:
            headers = {
                "Accept": "application/json",
            }
        return requests.request(
            url=self.url + path,
            auth=self.auth,
            method=method,
            params=params,
            json=json_payload,
            headers=headers,
        )

    def _get_item(self, item: str, local_folder: str, api_route: str) -> Optional[Dict]:
        local_storage = f'json_dumps/{local_folder}/{item}.json'
        if os.path.exists(local_storage):
            with open(local_storage, "r") as from_local:
                data = json.load(from_local)
        else:
            response = self._request(path=f'{api_route}/{item}')
            if response.ok:
                data = response.json()
                with open(local_storage, 'w') as to_local:
                    json.dump(data, to_local)
        return data

    def _get_all(self, path: str) -> Optional[List]:
        response = self._request(path=path)
        if response.ok:
            results = response.json().get('results', [])
            return [result.get('index') for result in results]


    def parse_spells_from_api_to_gsheet(self, gsheetName=SPELLS_SHEET_NAME) -> str:
        worksheet = self.sheet.worksheet(gsheetName)
        all_spells = self._get_all(path='spells/')

        parsed_spells = []
        headers = [
           'index', 'name', 'description', 'higher_level', 'range', 'components', 'material', 'area_of_effect_type', 'area_of_effect_size', 'ritual', 'duration', 'concentration', 'casting_time', 'level', 'attack_type', 'damage_type'
        ]
        headers.extend([f'damage_at_level_{str(i)}' for i in range(1, 21)])
        headers.extend([f'damage_at_slot_{str(i)}' for i in range(1, 10)])
        headers.extend([
            'school', 'bard', 'cleric', 'druid', 'fighter', 'monk', 'paladin', 'ranger', 'rogue', 'sorcerer', 'warlock', 'wizard'
        ])
        parsed_spells.append(headers)

        if len(all_spells) > 0:
            i = 1
            for spell in all_spells:
                print(f"parsing {i} of {len(all_spells)}: {spell}")
                spell_data = self._get_item(item=spell, local_folder='spells', api_route='spell/')
                name = spell_data.get('name', f"failed to parse: {spell}")
                description = '\n'.join(spell_data.get('desc', []))
                higher_level = '\n'.join(spell_data.get('higher_level', []))
                range_ = spell_data.get('range')
                components = ", ".join(spell_data.get('components', []))
                material = spell_data.get('material')
                area_of_effect = spell_data.get('area_of_effect', {})
                area_of_effect_type = area_of_effect.get('type')
                area_of_effect_size = area_of_effect.get('size')
                ritual = spell_data.get('ritual')
                duration = spell_data.get('duration')
                concentration = spell_data.get('concentration')
                casting_time = spell_data.get('casting_time')
                level = spell_data.get('level')
                attack_type = spell_data.get('attack_type')
                damage = spell_data.get('damage', {})
                damage_type = damage.get('damage_type', {}).get('name')
                damage_at_levels = damage.get('damage_at_character_level', {})
                damage_at_level = []
                for lvl in range(1, 21):
                    level_damage = damage_at_levels.get(str(lvl))
                    if level_damage:
                        damage_at_level.append(level_damage)
                    elif damage_at_level:
                        damage_at_level.append(damage_at_level[-1])
                    else:
                        damage_at_level.append('')
                damage_at_slots = damage.get('damage_at_slot_level', {})
                damage_at_slot = []
                for slot in range(1, 10):
                    slot_damage = damage_at_slots.get(str(slot))
                    if slot_damage:
                        damage_at_slot.append(slot_damage)
                    elif damage_at_slot:
                        damage_at_slot.append(damage_at_slot[-1])
                    else:
                        damage_at_slot.append('')

                school = spell_data.get('school', {}).get('name')
                classes_use = {class_.get('index'): True for class_ in spell_data.get('classes', [])}

                bard = classes_use.get('bard', False)
                cleric = classes_use.get('cleric', False)
                druid = classes_use.get('druid', False)
                fighter = classes_use.get('fighter', False)
                monk = classes_use.get('monk', False)
                paladin = classes_use.get('paladin', False)
                ranger = classes_use.get('ranger', False)
                rogue = classes_use.get('rogue', False)
                sorcerer = classes_use.get('sorcerer', False)
                warlock = classes_use.get('warlock', False)
                wizard = classes_use.get('wizard', False)
                row = [
                    spell, name, description, higher_level, range_,
                    components, material, area_of_effect_type, area_of_effect_size,
                    ritual, duration, concentration, casting_time,
                    level, attack_type, damage_type
                ]
                row.extend(damage_at_level)
                row.extend(damage_at_slot)
                row.extend([
                    school, bard, cleric, druid,
                    fighter, monk, paladin, ranger,
                    rogue, sorcerer, warlock, wizard
                ])

                parsed_spells.append(row)
                i += 1

            worksheet.clear()
            worksheet.append_rows(parsed_spells)
            return 'jobs done'
        return 'failed to get spells list'

    @staticmethod
    def parse_spells_from_csv_to_sql_file(path_to_csv: str) -> str:
        with open(path_to_csv, newline='') as csv_file:
            csv_reader = csv.reader(csv_file)
            headers = next(csv_reader)
            with open('output.sql', 'w') as output:
                print(f"INSERT INTO public.spells ({', '.join(headers)}) \nVALUES", file=output, end='\n')
            for row in csv_reader:
                row_without_double_quotation = list(
                    map(
                        lambda value: value.replace('"', "'"), row
                    )
                )
                sql_row_values = list(
                    map(
                        lambda value: "null" if value == "" else value if value in ("TRUE", "FALSE") or value.isdigit() else f'"{str(value)}"',
                        row_without_double_quotation
                    )
                )
                with open('output.sql', 'a') as output:
                    print(f'({", ".join(sql_row_values)})', end=",\n",
                          file=output)
            return 'jobs done'

    def parse_spell_library_json(self, path) -> str:
        worksheet = self.sheet.worksheet('Spells from Spell Library Json')
        parsed_spells = [[
            'name', 'description', 'range', 'components',
            'material', 'ritual',
            'duration', 'casting_time', 'level', 'school',
            'bard', 'cleric', 'druid', 'fighter', 'monk', 'paladin', 'ranger',
            'rogue', 'sorcerer', 'warlock', 'wizard', 'subclass_only', 'subclasses_list', 'source'

        ]]
        with open(path, "r") as spell_library:
            all_spells = json.load(spell_library)

        for spell in all_spells.values():
            name = spell.get('Name')
            description = spell.get('Description')
            range = spell.get('Range')
            components_full = spell.get('Components', '')
            components_splitted = components_full.split(" (") if " M (" in components_full else None
            components = components_splitted[0] if components_splitted else components_full
            material = components_splitted[1].replace(")", "") if components_splitted else ""
            ritual = spell.get('Ritual')
            duration = spell.get('Duration')
            casting_time = spell.get('CastingTime')
            level = spell.get('Level')
            school = spell.get('School')
            classes_use = {class_.split(" ")[0]: True for class_ in spell.get('Classes', [])}
            bard = classes_use.get('Bard', False)
            cleric = classes_use.get('Cleric', False)
            druid = classes_use.get('Druid', False)
            fighter = classes_use.get('Fighter', False)
            monk = classes_use.get('Monk', False)
            paladin = classes_use.get('Paladin', False)
            ranger = classes_use.get('Ranger', False)
            rogue = classes_use.get('Rogue', False)
            sorcerer = classes_use.get('Sorcerer', False)
            warlock = classes_use.get('Warlock', False)
            wizard = classes_use.get('Wizard', False)
            all_classes = [class_.split(" ")[0].lower() for class_ in spell.get('Classes', [])]
            subclass_only = ', '.join([class_.split(" ")[0].lower() for class_ in spell.get('Classes', []) if " (" in class_ and all_classes.count(class_.split(" ")[0].lower()) == 1])
            subclasses_list = ', '.join([re.sub(r'[()]', '',class_.split(" ")[1]).lower() for class_ in spell.get('Classes', []) if " (" in class_ and all_classes.count(class_.split(" ")[0].lower()) == 1])
            source = spell.get('Source')
            parsed_spells.append(
                [
                    name, description, range, components, material, ritual, duration, casting_time, level, school,
                    bard, cleric, druid,
                    fighter, monk, paladin, ranger,
                    rogue, sorcerer, warlock, wizard, subclass_only, subclasses_list, source
                ]
            )
        worksheet.clear()
        worksheet.append_rows(parsed_spells)
        return 'jobs done'

    def parse_classes_from_api_to_gsheet(self) -> str:
        worksheet = self.sheet.worksheet(CLASS_SHEET_NAME)

        all_classes = self._get_all('classes/')
        all_skills = self._get_all('skills/')
        if len(all_classes) and len(all_skills) > 0:

            headers = [
               'index', 'name', 'hit_die', 'proficiency_choices_description', 'proficiency_choices_choose', 'proficiences_indices', 'proficiences_names'
            ]
            headers.extend(
                [skill for skill in all_skills]
            )
            headers.extend(['saving_throws', 'level', 'ability_score_bonuses', 'prof_bonus', 'features_indices', 'features_names', 'cantrips'])
            headers.extend([
                f'spell_slots_level_{i}'
                            for i in range(1, 10)
            ])
            parsed_classes = [headers]

            for class_ in all_classes:

                print(f'processing {class_}...', end='')

                class_details = self._get_item(item=class_, local_folder='classes', api_route='classes/')
                name = class_details.get('name')
                hit_die = class_details.get('hit_die')
                proficiencies_indices = ', '.join([proficiency.get('index') for proficiency in class_details.get('proficiencies', [])])
                proficiencies_names = ', '.join([proficiency.get('name') for proficiency in class_details.get('proficiencies', [])])
                proficiency_choices = class_details.get('proficiency_choices', [{}])

                if len(proficiency_choices) > 1:
                    print(f'{class_} has {len(proficiency_choices)} proficiency choices...', end='')

                proficiency_choices_description = proficiency_choices[0].get('desc')
                proficiency_choices_choose = proficiency_choices[0].get('choose')
                proficiency_options = {
                    skill.get('item', {}).get('index').replace('skill-',
                                                              '').lower(): True
                    for skill in
                    proficiency_choices[0].get('from', {}).get('options', [])
                    if 'skill-' in skill.get('item', {}).get('index')
                }
                all_profficiencies_skills = [
                    proficiency_options.get(skill, False) for skill in all_skills
                ]
                saving_throws = ', '.join([st.get('name') for st in class_details.get('saving_throws', [])])
                class_levels_response = self._request(path=f'classes/{class_}/levels')
                if class_levels_response.ok:
                    class_levels = class_levels_response.json()
                    for level in class_levels:
                        class_level = level.get('level')

                        if class_level == 1:
                            print('level 1', end='\n')
                        else:
                            print(f'processing {class_}...level {class_level}', end='\n')

                        ability_score_bonuses = level.get('ability_score_bonuses')
                        prof_bonus = level.get('prof_bonus')
                        features_indices = ', '.join([feature.get('index') for feature in level.get('features', [])])
                        features_names = ', '.join([feature.get('name') for feature in level.get('features', [])])
                        spellcasting_list = [level.get('spellcasting', {}).get('cantrips_known')]
                        spellcasting_list.extend([
                            level.get('spellcasting', {}).get(f'spell_slots_level_{i}')
                            for i in range(1, 10)
                        ])
                        row = [
                            class_, name, hit_die, proficiency_choices_description,
                            proficiency_choices_choose, proficiencies_indices, proficiencies_names,
                        ]
                        row.extend(all_profficiencies_skills)
                        row.extend([saving_throws, class_level, ability_score_bonuses, prof_bonus, features_indices, features_names])
                        row.extend(spellcasting_list)
                        parsed_classes.append(row)
            worksheet.clear()
            worksheet.append_rows(parsed_classes)
            return 'jobs done'
        return f'failed to receive {" ".join([name for name, lst in zip(["all_skills", "all_classes"], [all_skills, all_classes]) if len(lst) == 0 ])}'

    def parse_races_from_api_to_gsheet(self) -> str:
        worksheet = self.sheet.worksheet(RACES_SHEET_NAME)
        abilities_list = ['STR', 'DEX', 'CON', 'WIS', 'INT', 'CHA']
        headers = [
            'index', 'name', 'speed'
        ]
        headers.extend([
            f'{ability}_mod' for ability in abilities_list
        ])
        headers.extend([
            'alignment', 'age', 'size', 'size_description', 'proficiencies_indices',
            'proficiencies_names', 'languages', 'language_desc', 'traits_indices', 'traits_names'
        ])

        parsed_data = [headers]
        all_races = self._get_all('races/')
        if len(all_races) > 0:
            for race in all_races:

                print(f'collecting {race} data')

                race_details = self._get_item(item=race, local_folder='races', api_route='races/')

                name = race_details.get('name')
                speed = race_details.get('speed')
                ability_bonuses = race_details.get('ability_bonuses')
                all_abilities = {
                    ability_bonus.get('ability_score', {}).get('name'):  ability_bonus.get('bonus')
                    for ability_bonus in ability_bonuses
                }
                ability_modifiers = [all_abilities.get(ability) for ability in abilities_list]
                alignment = race_details.get('alignment')
                age = race_details.get('age')
                size = race_details.get('size')
                size_description = race_details.get('size_description')
                proficiencies_indices = ', '.join([proficiency.get('index') for proficiency in race_details.get('starting_proficiencies')])
                proficiencies_names = ', '.join(
                    [proficiency.get('name') for proficiency in
                     race_details.get('starting_proficiencies')])
                languages = ', '.join(
                    [language.get('name') for language in
                     race_details.get('languages')])
                language_desc = race_details.get('language_desc')
                traits_indices = ', '.join([trait.get('index') for trait in race_details.get('traits')])
                traits_names = ', '.join([trait.get('name') for trait in race_details.get('traits')])
                row = [race, name, speed]
                row.extend(ability_modifiers)
                row.extend([alignment, age, size, size_description, proficiencies_indices,
            proficiencies_names, languages, language_desc, traits_indices, traits_names])

                parsed_data.append(row)
            worksheet.clear()
            worksheet.append_rows(parsed_data)
            return 'jobs done'
        return 'failed to receive races list'

    def parse_features_from_api_to_gsheet(self) -> str:
        worksheet = self.sheet.worksheet(FEATURES_SHEET_NAME)
        headers = [
            'index', 'name', 'class_index', 'description', 'level'
        ]
        parsed_data = [headers]
        all_features = self._get_all('features/')
        if len(all_features) > 0:
            for feature in all_features:

                print(f'processing {feature}')

                feature_data = self._get_item(item=feature, local_folder='features', api_route='features/')
                name = feature_data.get('name')
                class_index = feature_data.get('class', {}).get('index')
                desc = '\n'.join(feature_data.get('desc', []))
                level = feature_data.get('level')
                row = [
                    feature, name, class_index, desc, level
                ]
                parsed_data.append(row)
            worksheet.clear()
            worksheet.append_rows(parsed_data)
            return 'jobs done'
        return 'failed to get all features'

    def parse_traits_from_api_to_gsheet(self):
        worksheet = self.sheet.worksheet(TRAITS_SHEET_NAME)
        headers = [
            'index', 'name', 'description', 'races_indices', 'proficiencies_indices', 'proficiencies_names',
            'damage_type', 'area_of_effect_type', 'area_of_effect_size', 'usage_times', 'dc', 'dc_success'
        ]
        headers.extend([f'damage_at_{lvl}' for lvl in range(1, 21)])

        parsed_data = [headers]
        all_traits = self._get_all('traits/')
        if len(all_traits) > 0:
            for trait in all_traits:

                print(f'processing {trait}')

                trait_data = self._get_item(item=trait, local_folder='traits', api_route='traits/')
                name = trait_data.get('name')
                desc = '\n'.join(trait_data.get('desc', []))
                races = ', '.join([race.get('index') for race in
                                   trait_data.get('races', [])])
                profficiencies_indices = ', '.join([
                    profficiency.get('index') for profficiency in trait_data.get('proficiencies', [])
                ])
                profficiencies_names = ', '.join([
                    profficiency.get('name') for profficiency in trait_data.get('proficiencies', [])
                ])
                trait_specific = trait_data.get('trait_specific', {})
                damage_type = trait_specific.get('damage_type',{}).get('name')
                area_of_effect_type = trait_specific.get('breath_weapon',{}).get('area_of_effect',{}).get('type')
                area_of_effect_size = trait_specific.get('breath_weapon',
                                                         {}).get(
                    'area_of_effect', {}).get('size')
                usage_times = trait_specific.get('breath_weapon',{}).get('usage',{}).get('times')
                dc = trait_specific.get('breath_weapon',{}).get('dc',{}).get('dc_type',{}).get('name')
                dc_success = trait_specific.get('breath_weapon',{}).get('dc',{}).get('success_type')
                damage_data = trait_specific.get('breath_weapon',{}).get('damage',[])
                damage_at_levels = []
                if len(damage_data)>0:
                    for lvl in range(1,21):
                        damage_at_level = damage_data[0].get('damage_at_character_level',{}).get(str(lvl))
                        if damage_at_level:
                            damage_at_levels.append(damage_at_level)
                        elif damage_at_levels:
                            damage_at_levels.append(damage_at_levels[-1])
                        else:
                            damage_at_levels.append('')

                row = [trait, name, desc, races, profficiencies_indices, profficiencies_names, damage_type, area_of_effect_type,
                       area_of_effect_size, usage_times, dc, dc_success]
                row.extend(damage_at_levels)
                print(len(row), len(headers))

                parsed_data.append(row)
            worksheet.clear()
            worksheet.append_rows(parsed_data)
            return 'jobs done'

        return 'failed to get all traits'
