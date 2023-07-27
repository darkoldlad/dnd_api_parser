from parser import ParserToGsheet


def main():
    parser = ParserToGsheet()
    # spells_api_result = parser.parse_all_spells_from_api_to_gsheet()
    # csv_parsing_result = parser.parse_all_spells_from_csv_to_sql_file('DnD entities data - Spells.csv')
    # json_parsing_result = parser.parse_spell_library_json('Spell Library 11-16-19.JSON')
    classes_api_result = parser.parse_classes_from_api_to_gsheet()
    print(classes_api_result)


if __name__ == '__main__':
    main()
