import gspread
import requests
import csv
from google.oauth2 import service_account
from typing import Union, Dict, List, Optional

from config import GSPREAD_SCOPE, GSHEET_CREDENTIALS_PATH, URL_FOR_GSHEET, \
    SPELLS_SHEET_NAME


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

    def _get_spell(self, spell_name: str) -> Optional[Dict]:
        response = self._request(path=f'spells/{spell_name}')
        if response.ok:
            return response.json()

    def _get_all_spells(self, path: str = 'spells/') -> Optional[Dict]:
        response = self._request(path=path)
        if response.ok:
            return response.json()

    def parse_all_spells_from_api_to_gsheet(self, gsheetName=SPELLS_SHEET_NAME) -> str:
        worksheet = self.sheet.worksheet(gsheetName)
        spells_list_from_api = self._get_all_spells().get('results')
        all_spells = [
            spell.get('index') for spell in spells_list_from_api
        ]
        parsed_spells = []
        headers = [
            'name', 'description', 'higher_level', 'range', 'components', 'material', 'area_of_effect_type', 'area_of_effect_size', 'ritual', 'duration', 'concentration', 'casting_time', 'level', 'attack_type', 'damage_type'
        ]
        damage_at_level_headers = [f'damage_at_{str(i)}' for i in range(1, 21)]
        headers.extend(damage_at_level_headers)
        headers.extend([
            'school', 'bard', 'cleric', 'druid', 'paladin', 'ranger', 'sorcerer', 'warlock', 'wizard'
        ])

        i = 1
        if len(all_spells) > 0:
            for spell in all_spells:
                print(f"parsing {i} of {len(all_spells)}: {spell}")
                spell_data = self._get_spell(spell)
                name = spell_data.get('name', f"failed to parse{spell}")
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
                damage_at_levels = damage.get('damage_at_character_level') if damage.get('damage_at_character_level') else damage.get('damage_at_slot_level', {})
                damage_at_level = [damage_at_levels.get(str(i+1)) for i in range(20)]
                school = spell_data.get('school', {}).get('name')
                classes_use = {class_.get('index'): True for class_ in spell_data.get('classes', [])}

                bard = classes_use.get('bard', False)
                cleric = classes_use.get('cleric', False)
                druid = classes_use.get('druid', False)
                # fighter don't have spells
                # monk don't have spells
                paladin = classes_use.get('paladin', False)
                ranger = classes_use.get('ranger', False)
                # rogue don't have spells
                sorcerer = classes_use.get('sorcerer', False)
                warlock = classes_use.get('warlock', False)
                wizard = classes_use.get('wizard', False)
                row = [
                    name, description, higher_level, range_,
                    components, material, area_of_effect_type, area_of_effect_size,
                    ritual, duration, concentration, casting_time,
                    level, attack_type, damage_type
                ]
                row.extend(damage_at_level)
                row.extend([
                    school, bard, cleric, druid,
                    paladin, ranger,
                    sorcerer, warlock, wizard
                ])

                parsed_spells.append(row)
                i += 1

            worksheet.clear()
            worksheet.append_rows(parsed_spells)
            return 'success'
        return 'failed to get spells list'

    def parse_all_spells_from_csv_to_sql_file(self, path_to_csv) -> str:
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










