from parser import ParserToGsheet, Methods


def main():
    parser = ParserToGsheet()

    parser.parse_all(exceptions=[
        Methods.PARSE_SPELLS,
        Methods.PARSE_CLASSES,
        Methods.PARSE_RACES,
        Methods.PARSE_PROFICIENCIES,
        Methods.PARSE_TRAITS,
        Methods.PARSE_FEATURES,
        Methods.PARSE_SKILLS,
        Methods.PARSE_SUBRACES,
        # Methods.PARSE_SUBCLASSES,
    ])
    """
    parser.csv_to_sql(
        table_name='classes_skills',
        path_to_csv='csv/DnD entities data - Classes_Skills.csv'
    )
    """



if __name__ == '__main__':
    main()
