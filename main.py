from parser import Parser, Methods


def main():
    parser = Parser()

    parser.parse_all(exceptions=[
        Methods.PARSE_SPELLS,
        Methods.PARSE_CLASSES,
        Methods.PARSE_RACES,
        Methods.PARSE_PROFICIENCIES,
        Methods.PARSE_TRAITS,
        Methods.PARSE_FEATURES,
        Methods.PARSE_SKILLS,
        Methods.PARSE_SUBRACES,
        Methods.PARSE_SUBCLASSES,
        Methods.PARSE_EQUIPMENT,
        # Methods.PARSE_MAGIC_ITEMS,
    ])
    """
    parser.csv_to_sql(
        table_name='classes_skills',
        path_to_csv='csv/DnD entities data - Classes_Skills.csv'
    )
    """



if __name__ == '__main__':
    main()
