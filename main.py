from parser import ParserToGsheet


def main():
    parser = ParserToGsheet()
    # spells_api_result = parser.parse_spells_from_api_to_gsheet()
    # csv_parsing_result = parser.parse_spells_from_csv_to_sql_file('DnD entities data - Spells.csv')
    # json_parsing_result = parser.parse_spell_library_json('Spell Library 11-16-19.JSON')
    # classes_api_result = parser.parse_classes_from_api_to_gsheet()
    # races_api_result = parser.parse_races_from_api_to_gsheet()
    # traits_api_result = parser.parse_traits_from_api_to_gsheet()
    features_api_result = parser.parse_features_from_api_to_gsheet()
    print(features_api_result)


if __name__ == '__main__':
    main()
