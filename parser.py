import requests
import csv
import json
import re
import os
import inspect
from typing import Union, Dict, List, Optional
from enum import Enum

from config import SPELLS_SHEET_NAME, CLASS_SHEET_NAME, RACES_SHEET_NAME, FEATURES_SHEET_NAME, \
    TRAITS_SHEET_NAME, SKILLS_SHEET_NAME, \
    PROFICIENCIES_SHEET_NAME, SUBRACES_SHEET_NAME, SUBCLASSES_SHEET_NAME, \
    EQUIPMENT_SHEET_NAME, MAGIC_ITEMS_SHEET_NAME
from gsheet_service import Gsheet


class Methods(str, Enum):
    PARSE_SPELLS = 'parse_spells'
    PARSE_CLASSES = 'parse_classes'
    PARSE_RACES = 'parse_races'
    PARSE_TRAITS = 'parse_traits'
    PARSE_FEATURES = 'parse_features'
    PARSE_PROFICIENCIES = 'parse_proficiencies'
    PARSE_SKILLS = 'parse_skills'
    PARSE_SUBRACES = 'parse_subraces'
    PARSE_SUBCLASSES = 'parse_subclasses'
    PARSE_EQUIPMENT = 'parse_equipment'
    PARSE_MAGIC_ITEMS = 'parse_magic_items'


class Parser:
    def __init__(self, auth=None):
        self.sheet = Gsheet()
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

        root_dir = 'json_dumps'

        os.makedirs(
            os.path.join(
                root_dir, local_folder
            ),
            exist_ok=True
        )

        local_storage = os.path.join(root_dir, local_folder, f'{item}.json')

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

    def _get_all(self, route: str) -> Optional[List]:
        response = self._request(path=route)
        if response.ok:
            results = response.json().get('results', [])
            return [result.get('index') for result in results]

    def parse_spells(self, route: str = 'spells/') -> str:
        worksheet = self.sheet.get_worksheet(SPELLS_SHEET_NAME)
        all_spells = self._get_all(route=route)


        headers = [
           'index', 'name', 'description', 'higher_level', 'range', 'components', 'material', 'area_of_effect_type', 'area_of_effect_size', 'ritual', 'duration', 'concentration', 'casting_time', 'spell_level', 'school', 'class_index', 'attack_type', 'damage_type', 'damage_modifier', 'modifier_lvl', 'damage'
        ]

        rows = [headers]

        if len(all_spells) > 0:
            i = 1
            for spell in all_spells:
                print(f"parsing {i} of {len(all_spells)}: {spell}")
                spell_data = self._get_item(item=spell, local_folder='spells', api_route=route)
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
                school = spell_data.get('school', {}).get('name')
                attack_type = spell_data.get('attack_type')

                for class_ in spell_data.get('classes', [{}]):
                    class_index = class_.get('index')
                    damage = spell_data.get('damage', {})
                    damage_type = damage.get('damage_type', {}).get('name')
                    damage_at_levels = damage.get('damage_at_character_level')
                    damage_at_slots = damage.get('damage_at_slot_level')
                    damage_modifier = 'slot' if damage_at_slots else 'level' if damage_at_levels else ''

                    if damage_modifier == 'level':
                        level_keys = [int(key) for key in damage_at_levels.keys()]
                        prev_value = None
                        for lvl in range(min(level_keys), 21):
                            modifier_lvl = lvl
                            if lvl in level_keys:
                                prev_value = damage_at_levels.get(f'{lvl}')
                            damage_value = prev_value
                            row = [spell, name, description, higher_level, range_, components, material, area_of_effect_type, area_of_effect_size, ritual, duration, concentration, casting_time, level, school, class_index, attack_type, damage_type, damage_modifier, modifier_lvl, damage_value]
                            rows.append(row)

                    elif damage_modifier == 'slot':
                        slot_keys = [int(key) for key in damage_at_slots.keys()]
                        prev_value = None
                        for slot in range(level, max(slot_keys)+1):
                            modifier_lvl = slot
                            if slot in slot_keys:
                                prev_value = damage_at_slots.get(f'{slot}')
                            damage_value = prev_value
                            row = [spell, name, description, higher_level, range_, components, material, area_of_effect_type, area_of_effect_size, ritual, duration, concentration, casting_time, level, school, class_index, attack_type, damage_type, damage_modifier, modifier_lvl, damage_value]
                            rows.append(row)

                    else:
                        row = [spell, name, description, higher_level, range_, components, material, area_of_effect_type, area_of_effect_size, ritual, duration, concentration, casting_time, level, school, class_index, attack_type, damage_type, damage_modifier, '', '']
                        rows.append(row)
                i+=1
            worksheet.clear()
            worksheet.append_rows(rows)
            return 'jobs done'
        return 'failed to get spells list'

    @staticmethod
    def csv_to_sql(path_to_csv: str, table_name: str, dataset: str = 'core') -> str:
        with open(path_to_csv, newline='') as csv_file:
            csv_reader = csv.reader(csv_file)

            headers = next(csv_reader)
            rows = list(csv_reader)

            with open('output.sql', 'w') as output:
                print(f"INSERT INTO {dataset}.{table_name} ({', '.join(headers)}) \nVALUES", file=output, end='\n')
            for row in rows:
                row_with_correct_single_quotation = list(
                    map(
                        lambda value: value.replace("'", "''"), row
                    )
                )


                sql_row_values = list(
                    map(
                        lambda value: "null" if value == "" else value if value in ("TRUE", "FALSE") or value.isdigit() else f"'{str(value)}'",
                        row_with_correct_single_quotation
                    )
                )
                with open('output.sql', 'a') as output:
                    print(f'({", ".join(sql_row_values)})', end=",\n" if rows.index(row) != len(rows)-1 else ';',
                          file=output)
            return 'jobs done'

    def parse_spell_library_json(self, path) -> str:
        worksheet = self.sheet.get_worksheet('Spells from Spell Library Json')
        rows = [[
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
            rows.append(
                [
                    name, description, range, components, material, ritual, duration, casting_time, level, school,
                    bard, cleric, druid,
                    fighter, monk, paladin, ranger,
                    rogue, sorcerer, warlock, wizard, subclass_only, subclasses_list, source
                ]
            )
        worksheet.clear()
        worksheet.append_rows(rows)
        return 'jobs done'

    def parse_classes(self, route: str = 'classes/') -> str:
        worksheet = self.sheet.get_worksheet(CLASS_SHEET_NAME)

        all_classes = self._get_all(route)
        classes_skills = [['class_index', 'proficiency_skills_description', 'skills_choose', 'skill_index']]
        if len(all_classes) > 0:

            headers = [
               'index', 'name', 'hit_die',
                'saving_throws', 'level', 'ability_score_bonuses', 'ability_score_bonuses_total', 'proficiency_bonus', 'features_names', 'is_caster', 'cantrips'
            ]
            headers.extend([
                f'spell_slots_level_{i}'
                            for i in range(1, 10)
            ])
            rows = [headers]

            for class_ in all_classes:

                print(f'processing {class_}...', end='')

                class_details = self._get_item(item=class_, local_folder='classes', api_route=route)
                name = class_details.get('name')
                hit_die = class_details.get('hit_die')

                proficiencies_skills = class_details.get('proficiency_choices', [{}])

                if len(proficiencies_skills) > 1:
                    print(f'{class_} has {len(proficiencies_skills)} proficiency choices...', end='')

                proficiency_skills_description = proficiencies_skills[0].get('desc')
                proficiency_skills_choose = proficiencies_skills[0].get('choose')

                saving_throws = ', '.join([st.get('name') for st in class_details.get('saving_throws', [])])

                possible_skills = proficiencies_skills[0].get('from', {}).get('options', [{}])

                for skill in possible_skills:
                    possible_skill = skill.get('item', {}).get('index', 'skill-').replace('skill-', '')
                    classes_skills.append([
                        class_, proficiency_skills_description, proficiency_skills_choose, possible_skill
                    ])

                class_levels_response = self._request(path=f'{route + class_}/levels')

                if class_levels_response.ok:
                    class_levels = class_levels_response.json()
                    available_spells = [class_level.get('spellcasting', {}) for class_level in class_levels]
                    spells = [casting_level.get('cantrips_known') for casting_level in available_spells]
                    spells.extend([
                        casting_level.get(f'spell_slots_level_{i}') for casting_level
                        in available_spells for i in range(1, 10)
                    ])
                    is_caster = any(spell for spell in spells)
                    prev_ability_score_bonus = 0
                    for level in class_levels:

                        class_level = level.get('level')

                        spellcasting_list = [level.get('spellcasting', {}).get('cantrips_known')]
                        spellcasting_list.extend([
                            level.get('spellcasting', {}).get(f'spell_slots_level_{i}')
                            for i in range(1, 10)
                        ])

                        level_ability_score_bonus = level.get('ability_score_bonuses')
                        ability_score_bonuses = level_ability_score_bonus - prev_ability_score_bonus

                        if level_ability_score_bonus > prev_ability_score_bonus:
                            prev_ability_score_bonus = level_ability_score_bonus


                        prof_bonus = level.get('prof_bonus')

                        features_names = ', '.join([feature.get('name') for feature in level.get('features', [])])

                        if class_level == 1:

                            print('level 1', end='\n')

                        else:
                            print(f'processing {class_}...level {class_level}', end='\n')
                        row = [
                            class_, name, hit_die, saving_throws, class_level, ability_score_bonuses, level_ability_score_bonus, prof_bonus,
                                    features_names, is_caster]
                        row.extend(spellcasting_list)
                        rows.append(row)

            worksheet.clear()
            worksheet.append_rows(rows)

            classes_skills_worksheet = self.sheet.get_worksheet('Classes_Skills')
            classes_skills_worksheet.clear()
            classes_skills_worksheet.append_rows(classes_skills)

            return 'jobs done'
        return 'failed to receive all classes'

    def parse_races(self, route: str = 'races/') -> str:
        worksheet = self.sheet.get_worksheet(RACES_SHEET_NAME)
        abilities_list = ['STR', 'DEX', 'CON', 'WIS', 'INT', 'CHA']
        headers = [
            'index', 'name', 'speed'
        ]
        headers.extend([
            f'{ability}_mod' for ability in abilities_list
        ])
        headers.extend([
            'alignment', 'age', 'size', 'size_description',
            'proficiencies_names', 'languages', 'language_desc', 'traits_names'
        ])

        rows = [headers]

        all_races = self._get_all(route)

        if len(all_races) > 0:
            for race in all_races:

                print(f'collecting {race} data')

                race_details = self._get_item(item=race, local_folder='races', api_route=route)

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

                proficiencies_names = ', '.join(
                    [proficiency.get('name') for proficiency in
                     race_details.get('starting_proficiencies')])
                languages = ', '.join(
                    [language.get('name') for language in
                     race_details.get('languages')])
                language_desc = race_details.get('language_desc')

                traits_names = ', '.join([trait.get('name') for trait in race_details.get('traits')])
                row = [race, name, speed]
                row.extend(ability_modifiers)
                row.extend([alignment, age, size, size_description,
            proficiencies_names, languages, language_desc, traits_names])

                rows.append(row)
            worksheet.clear()
            worksheet.append_rows(rows)
            return 'jobs done'
        return 'failed to receive races list'

    def parse_features(self, route: str = 'features/') -> str:
        worksheet = self.sheet.get_worksheet(FEATURES_SHEET_NAME)
        headers = [
            'index', 'name', 'class_index', 'subclass_index', 'description', 'level'
        ]
        rows = [headers]

        all_features = self._get_all(route)

        if len(all_features) > 0:
            for feature in all_features:

                print(f'processing {feature}')

                feature_data = self._get_item(item=feature, local_folder='features', api_route=route)
                name = feature_data.get('name')
                class_index = feature_data.get('class', {}).get('index')
                subclass_index = feature_data.get('subclass', {}).get('index')
                desc = '\n'.join(feature_data.get('desc', []))
                level = feature_data.get('level')
                row = [
                    feature, name, class_index, subclass_index, desc, level
                ]
                rows.append(row)
            worksheet.clear()
            worksheet.append_rows(rows)
            return 'jobs done'
        return 'failed to get all features'

    def parse_traits(self, route: str = 'traits/') -> str:
        worksheet = self.sheet.get_worksheet(TRAITS_SHEET_NAME)
        headers = [
            'index', 'name', 'description', 'race_index', 'subrace_index', 'proficiency_index', 'is_damage',
            'damage_type', 'area_of_effect_type', 'area_of_effect_size', 'usage_times', 'dc', 'dc_success', 'level', 'damage'
        ]

        rows = [headers]

        all_traits = self._get_all(route)

        if len(all_traits) > 0:
            for trait in all_traits:

                print(f'processing {trait}')

                trait_data = self._get_item(item=trait, local_folder='traits', api_route=route)
                name = trait_data.get('name')
                desc = '\n'.join(trait_data.get('desc', []))
                race_indices = trait_data.get('races', []) if len(trait_data.get('races', [])) > 0 else [{'index':''}]
                subrace_indices = trait_data.get('subraces', []) if len(trait_data.get('subraces', [])) > 0 else [{'index': ''}]
                proficiencies_indices = trait_data.get('proficiencies', []) if len(trait_data.get('proficiencies', [])) > 0 else [{'index':''}]

                for race in race_indices:
                    race_index=race.get('index')
                    for subrace in subrace_indices:
                        subrace_index = subrace.get('index')
                        for proficiency in proficiencies_indices:
                            proficiency_index = proficiency.get('index')
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

                            is_damage = True if len(damage_data) > 0 else False
                            prev_damage = ''
                            damage = ''
                            level = ''
                            if is_damage:
                                for lvl in range(1,21):
                                    level = lvl
                                    damage_at_level = damage_data[0].get('damage_at_character_level',{}).get(str(lvl))
                                    if damage_at_level:
                                        damage = damage_at_level
                                        prev_damage = damage_at_level
                                    elif prev_damage:
                                        damage = prev_damage

                                    row = [trait, name, desc, race_index, subrace_index, proficiency_index, is_damage, damage_type, area_of_effect_type,
                                           area_of_effect_size, usage_times, dc, dc_success, level, damage, ]
                                    rows.append(row)
                            else:
                                row = [trait, name, desc, race_index, subrace_index, proficiency_index, is_damage, damage_type, area_of_effect_type,
                                       area_of_effect_size, usage_times, dc, dc_success, level, damage, ]
                                rows.append(row)
            worksheet.clear()
            worksheet.append_rows(rows)
            return 'jobs done'

        return 'failed to get all traits'

    def parse_proficiencies(self, route: str ='proficiencies/') -> str:
        worksheet = self.sheet.get_worksheet(PROFICIENCIES_SHEET_NAME)

        headers = ['index', 'name', 'reference_type', 'class_index', 'race_index', 'reference_index', 'reference_url']
        rows = [headers]

        all_proficiencies = self._get_all(route)

        if len(all_proficiencies) > 0:
            for proficiency in all_proficiencies:

                print(f'processing {proficiency}')

                proficiency_data = self._get_item(item=proficiency, local_folder='proficiencies', api_route=route)
                name = proficiency_data.get('name')
                reference_type = proficiency_data.get('type')
                reference_index = proficiency_data.get('reference', {}).get('index')
                reference_url = proficiency_data.get('reference', {}).get('url')
                proficiency_classes = proficiency_data.get('classes', []) if len(proficiency_data.get('classes', [])) > 0 else [{'index': ''}]
                proficiency_races = proficiency_data.get('races', []) if len(proficiency_data.get('races', [])) > 0 else [{'index': ''}]
                for race in proficiency_races:
                    race_index = race.get('index')
                    for class_ in proficiency_classes:
                        class_index = class_.get('index')
                        row = [
                            proficiency, name, reference_type, class_index, race_index, reference_index, reference_url
                        ]
                        rows.append(row)
            worksheet.clear()
            worksheet.append_rows(rows)
            return 'jobs done'

        return 'failed to get all proficiencies'

    def parse_skills(self, route: str = 'skills/') -> str:
        worksheet = self.sheet.get_worksheet(SKILLS_SHEET_NAME)
        headers = ['index', 'name', 'ability_score', 'description']
        rows = [headers]

        all_skills = self._get_all(route)

        if len(all_skills) > 0:
            for skill in all_skills:
                skill_data = self._get_item(item=skill, local_folder='skills', api_route=route)

                print(f'processing {skill}')

                name = skill_data.get('name')
                ability_score = skill_data.get('ability_score', {}).get('name')
                description = '\n'.join(skill_data.get('desc', []))

                row = [skill, name, ability_score, description]
                rows.append(row)
            worksheet.clear()
            worksheet.append_rows(rows)
            return 'jobs done'

        return 'failed to get all skills'

    def parse_subraces(self, route: str = 'subraces/') -> str:
        worksheet = self.sheet.get_worksheet(SUBRACES_SHEET_NAME)
        abilities_list = ['STR', 'DEX', 'CON', 'WIS', 'INT', 'CHA']
        headers = ['index', 'name']
        headers.extend([
            f'{ability}_mod' for ability in abilities_list
        ])
        headers.extend(['description', 'race_index', 'traits_names', 'proficiencies_names'])
        rows = [headers]
        all_subraces = self._get_all(route)

        if len(all_subraces) > 0:
            for subrace in all_subraces:

                print(f'processing {subrace}')

                subrace_data = self._get_item(item=subrace, local_folder='subraces', api_route=route)
                name = subrace_data.get('name')
                ability_bonuses = subrace_data.get('ability_bonuses', [{}])
                all_abilities = {
                    ability_bonus.get('ability_score', {}).get('name'): ability_bonus.get('bonus')
                    for ability_bonus in ability_bonuses
                }
                ability_modifiers = [all_abilities.get(ability) for ability in abilities_list]
                description = subrace_data.get('desc')
                race_index = subrace_data.get('race', {}).get('index')
                traits = ', '.join([trait.get('name') for trait in subrace_data.get('racial_traits', [{}])])
                proficiencies = ', '.join([prof.get('name') for prof in subrace_data.get('starting_proficiencies', [{}])])
                row = [subrace, name]
                row.extend(ability_modifiers)
                row.extend([description, race_index, traits, proficiencies])
                rows.append(row)
            worksheet.clear()
            worksheet.append_rows(rows)
            return 'jobs done'
        return 'failed to get all subraces'

    def parse_subclasses(self, route: str = 'subclasses/') -> str:
        worksheet = self.sheet.get_worksheet(SUBCLASSES_SHEET_NAME)
        all_subclasses = self._get_all(route)

        subclasses_spells = [['subclass_index', 'spell_index', 'class_index', 'class_level']]

        if len(all_subclasses) > 0:

            headers = [
                'index', 'name', 'description', 'class_index', 'subclass_flavor',
                 'level',
                'features_names',
            ]

            rows = [headers]

            for subclass in all_subclasses:

                print(f'processing {subclass}...', end='')

                subclass_details = self._get_item(item=subclass,
                                               local_folder='subclasses',
                                               api_route=route)
                name = subclass_details.get('name')
                description = '\n'.join(subclass_details.get('desc', []))
                class_index = subclass_details.get('class',{}).get('index')
                subclass_flavor = subclass_details.get('subclass_flavor')

                available_spells = subclass_details.get('spells', [])
                if len(available_spells) > 0:
                    for spell in available_spells:
                        subclasses_spells.append([
                            subclass, spell.get('spell', {}).get('index'), class_index, spell.get('prerequisites', [{}])[0].get('index').replace(f'{class_index}-', '')
                        ])

                subclass_levels_response = self._request(
                    path=f'{route + subclass}/levels')

                if subclass_levels_response.ok:
                    subclass_levels = subclass_levels_response.json()

                    for level in subclass_levels:

                        subclass_level = level.get('level')

                        features_names = ', '.join(
                            [feature.get('name') for feature in
                             level.get('features', [])])

                        if subclass_level == 1:

                            print('level 1', end='\n')

                        else:
                            print(f'processing {subclass}...level {subclass_level}',
                                  end='\n')
                        row = [
                            subclass, name, description, class_index, subclass_flavor, subclass_level,
                            features_names]

                        rows.append(row)
            worksheet.clear()
            worksheet.append_rows(rows)

            subclasses_spells_sheet = self.sheet.get_worksheet('Subclasses_Spells')
            subclasses_spells_sheet.clear()
            subclasses_spells_sheet.append_rows(subclasses_spells)

            return 'jobs done'
        return 'failed to receive all classes'

    def parse_equipment(self, route: str = 'equipment/') -> str:

        worksheet = self.sheet.get_worksheet(EQUIPMENT_SHEET_NAME)
        equipment_list = self._get_all(route)

        if len(equipment_list) > 0:
            rows = [[
                'index', 'name', 'category_index', 'cost', 'weight', 'weapon_category', 'weapon_range', 'damage_dice', 'damage_type', 'range_normal', 'range_long', 'properties_indices', '2h_damage_dice', '2h_damage_type',
                'armor_category', 'ac', 'ac_dex_bonus', 'str_min', 'stealth_disadvantage'
            ]]

            for item in equipment_list:

                print(f'processing {item}')

                item_details = self._get_item(item=item, local_folder='equipment', api_route=route)
                rows.append([
                    item,
                    item_details.get('name'),
                    item_details.get('equipment_category', {}).get('index'),
                    f"{item_details.get('cost', {}).get('quantity')} {item_details.get('cost', {}).get('unit')}",
                    item_details.get('weight'),
                    item_details.get('weapon_category'),
                    item_details.get('weapon_range'),
                    item_details.get('damage', {}).get('damage_dice'),
                    item_details.get('damage', {}).get('damage_type', {}).get('name'),
                    item_details.get('range', {}).get('normal'),
                    item_details.get('range', {}).get('long'),
                    ", ".join([property_.get('index') for property_ in item_details.get('properties', [{}])]),
                    item_details.get('two_handed_damage',{}).get('damage_dice'),
                    item_details.get('two_handed_damage', {}).get(
                        'damage_type', {}).get('name'),
                    item_details.get('armor_category'),
                    item_details.get('armor_class', {}).get('base'),
                    item_details.get('armor_class', {}).get('max_bonus') if item_details.get('armor_class', {}).get('dex_bonus') else 0,
                    item_details.get('str_minimum'),
                    item_details.get('stealth_disadvantage'),
                ])

            worksheet.clear()
            worksheet.append_rows(rows)
            return 'jobs done'
        return 'failed to get all items'

    def parse_magic_items(self, route:str = 'magic-items/') -> str:

        worksheet = self.sheet.get_worksheet(MAGIC_ITEMS_SHEET_NAME)
        all_items = self._get_all(route)

        if len(all_items) > 0:
            rows = [[
              'index', 'name', 'description', 'category_index', 'rarity', 'variant', 'has_children','parent_index'
            ]]

            parent_indices = {}

            for item in all_items:

                print(f'processing {item}')

                item_details = self._get_item(item=item, local_folder='magic_items', api_route=route)

                children_indices = [var.get('index') for var in
                     item_details.get('variants', [{}])]
                if len(children_indices)>0:
                    for indx in children_indices:
                        parent_indices[indx] = item

                rows.append([
                    item,
                    item_details.get('name'),
                    ", ".join(
                               item_details.get('desc', [])),
                    item_details.get('equipment_category', {}).get('index'),
                    item_details.get('rarity',{}).get('name'),
                    item_details.get('variant'),
                    True if len(item_details.get('variants',[])) > 0 else False,
                    parent_indices.get(item),
                ])
            worksheet.clear()
            worksheet.append_rows(rows)
            return 'jobs done'
        return 'failed to get all magic items'

    def parse_all(self, exceptions: Union[List[Methods], None] = None):

        exceptions_const = ['__init__', 'parse_all', '_request', '_get_all', '_get_item', 'csv_to_sql',
                            'parse_spell_library_json']
        all_methods = [name for name, method in inspect.getmembers(self, inspect.ismethod) if name not in exceptions_const]

        for method_name in all_methods:
            if method_name not in exceptions:

                print(f'Launching {method_name}')

                method = getattr(self, method_name)

                result = method()
                if result:
                    print(result)
