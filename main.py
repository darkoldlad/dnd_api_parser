from parser import ParserToGsheet


def main():
    parser = ParserToGsheet()
    spells_api_result = parser.parse_spells()
    print(spells_api_result)
    # csv_parsing_result = parser.parse_spells_from_csv_to_sql_file('DnD entities data - Spells.csv')
    # json_parsing_result = parser.parse_spell_library_json('Spell Library 11-16-19.JSON')
    classes_api_result = parser.parse_classes()
    print(classes_api_result)
    races_api_result = parser.parse_races()
    print(races_api_result)
    traits_api_result = parser.parse_traits()
    print(traits_api_result)
    features_api_result = parser.parse_features()
    print(features_api_result)


if __name__ == '__main__':
    main()
