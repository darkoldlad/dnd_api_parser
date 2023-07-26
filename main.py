from parser import ParserToGsheet


if __name__ == '__main__':
    parser = ParserToGsheet()
    # result = parser.parse_all_spells_from_api_to_gsheet()
    result = parser.parse_all_spells_from_csv_to_sql_file('DnD entities data - Spells.csv')
    print(result)
