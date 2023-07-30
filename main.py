from parser import ParserToGsheet, Methods


def main():
    parser = ParserToGsheet()

    parser.parse_all(exceptions=[
        Methods.PARSE_SPELLS,
        # Methods.PARSE_CLASSES,
        Methods.PARSE_RACES,
        Methods.PARSE_PROFICIENCIES,
        Methods.PARSE_TRAITS,
        Methods.PARSE_FEATURES,
        Methods.PARSE_SKILLS,
        Methods.PARSE_SUBRACES,
    ])


if __name__ == '__main__':
    main()
