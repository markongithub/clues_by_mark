from collections.abc import Callable, Generator
from itertools import product, combinations

CRIMINAL = True
INNOCENT = False


class FakeHypothesis:
    def __init__(self) -> None:
        self.queried_suspects = set()

    def get(self, suspect: str) -> bool:
        self.queried_suspects.add(suspect)
        return CRIMINAL


class Puzzle:
    def __init__(self, suspects: list[str], known: dict[str, bool]) -> None:
        self.suspects = suspects
        self.known = known
        self.neighbors_cache = {
            suspect: neighbors(list(suspects), suspect) for suspect in suspects
        }
        self.rules = {}

    def get_neighbors(self, suspect: str) -> list[str]:
        return self.neighbors_cache[suspect]

    def get_common_neighbors(self, suspects: list[str]) -> list[str]:
        return set.intersection(
            *[set(self.get_neighbors(suspect)) for suspect in suspects]
        )

    def add_rule(
        self, rule_name: str, guilt: bool, rule: Callable[[dict[str, bool]], bool]
    ) -> None:
        if guilt is not None:
            self.known[rule_name] = guilt
        self.rules[rule_name] = rule

    def equal_criminal_neighbors(
        self, rule_name: str, guilt: bool, suspect1: str, suspect2: str
    ) -> None:
        def rule(hypothesis: dict[str, bool]) -> bool:
            return count_criminal(
                self.get_neighbors(suspect1), hypothesis
            ) == count_criminal(self.get_neighbors(suspect2), hypothesis)

        self.add_rule(rule_name, guilt, rule)

    def equal_innocent_neighbors(
        self, rule_name: str, guilt: bool, suspect1: str, suspect2: str
    ) -> None:
        def rule(hypothesis: dict[str, bool]) -> bool:
            return count_innocent(
                self.get_neighbors(suspect1), hypothesis
            ) == count_innocent(self.get_neighbors(suspect2), hypothesis)

        self.add_rule(rule_name, guilt, rule)

    def more_criminal_neighbors(
        self, rule_name: str, guilt: bool, suspect1: str, suspect2: str
    ) -> None:
        def rule(hypothesis: dict[str, bool]) -> bool:
            return count_criminal(
                self.get_neighbors(suspect1), hypothesis
            ) > count_criminal(self.get_neighbors(suspect2), hypothesis)

        self.add_rule(rule_name, guilt, rule)

    def criminals_connected(
        self, rule_name: str, guilt: bool, suspects: list[str]
    ) -> None:
        # print(f"criminals_connected: {rule_name} {guilt} {suspects}")

        def rule(hypothesis: dict[str, bool]) -> bool:
            criminals = [
                suspect for suspect in suspects if hypothesis.get(suspect) == CRIMINAL
            ]
            if len(criminals) == 0:
                # I feel like this shouldn't happen but maybe?
                return True
            indices = [suspects.index(suspect) for suspect in criminals]
            index_distance = max(indices) - min(indices)
            return index_distance in [len(criminals) - 1, 4 * (len(criminals) - 1)]

        self.add_rule(rule_name, guilt, rule)

    def solve(self) -> None:
        fewer_suspects = set.union(
            *[relevant_suspects(rule) for rule in self.rules.values()]
        )
        for suspect in fewer_suspects:
            if suspect not in self.suspects:
                print(f"I think you misspelled someone in here: {suspect}")
                return
        rule_matrix = {}
        for rule_name, rule in self.rules.items():
            rule_matrix[rule_name] = [
                hypothesis
                for hypothesis in all_hypotheses(self.known, fewer_suspects)
                if rule(hypothesis)
            ]
        print("finished building rule matrix")
        maximum_number_of_combinations = 2 ** (
            len(fewer_suspects) - len(self.known.keys())
        )
        rules_to_remove = []
        for k, v in rule_matrix.items():
            # print(f"rule {k} has {len(v)}/{maximum_number_of_combinations} combinations")
            if len(v) == maximum_number_of_combinations:
                print(f"{k}'s rule is always true so we can ignore it.")
                rules_to_remove.append(k)
            if len(v) == 0:
                print(f"{k}'s rule is always false so this puzzle is unsolvable.")
                return
        for rule_name in rules_to_remove:
            del rule_matrix[rule_name]
        # print(rule_matrix)
        # rule_matrix is a dictionary of rule names to lists of hypotheses
        # we want to find the commonalities of the hypotheses for each rule combination
        for num_rules in range(1, len(rule_matrix) + 1):
            print(f"checking combinations of {num_rules} rules")
            for rule_combination in combinations(rule_matrix.keys(), num_rules):
                # print(f"rule_combination: {rule_combination}")
                set_of_frozensets_of_pairs = combine_rules_from_matrix(
                    [rule_matrix[rule] for rule in rule_combination]
                )
                list_of_dictionaries = [dict(f) for f in set_of_frozensets_of_pairs]
                # print(f"{rule_combination}: {sorted([sorted(d.items()) for d in list_of_dictionaries])}")
                commonalities_without_knowns = {
                    k: v
                    for k, v in find_commonalities(list_of_dictionaries).items()
                    if k not in self.known.keys()
                }
                if commonalities_without_knowns:
                    print(
                        f"{rule_combination} commonalities: {commonalities_without_knowns}"
                    )
        # for rule_name, lineups in rule_matrix.items():
        #    commonalities_without_knowns = {k: v for k,v in find_commonalities(lineups).items() if k not in known.keys()}
        #    print(f"{rule_name}: {commonalities_without_knowns}")


def my_first_rule(hypothesis: dict[str, bool]) -> bool:
    return hypothesis.get("Alice") == CRIMINAL and hypothesis.get("Bob") == INNOCENT


def relevant_suspects(rule: Callable[[dict[str, bool]], bool]) -> set[str]:
    fake_hypothesis = FakeHypothesis()
    _ = rule(fake_hypothesis)
    return fake_hypothesis.queried_suspects


def all_hypotheses(
    known: dict[str, bool], suspects: set[str]
) -> Generator[dict[str, bool], None, None]:
    unknown_suspects = sorted(suspects.difference(known.keys()))
    for assignment in product((CRIMINAL, INNOCENT), repeat=len(unknown_suspects)):
        hypothesis = known.copy()
        hypothesis.update(dict(zip(unknown_suspects, assignment)))
        yield hypothesis


def neighbors(all_suspects: list[str], suspect: str) -> list[str]:
    # 0 1 2 3
    # 4 5 6 7
    # 8 9 10 11
    # 12 13 14 15
    # 16 17 18 19
    my_index = all_suspects.index(suspect)
    # print(f"index of {suspect}:  {my_index}")
    row = my_index // 4
    column = my_index % 4
    # we need the indices of the neighbors, including diagonals
    candidate_indices = set(
        [
            my_index - 5,
            my_index - 4,
            my_index - 3,
            my_index - 1,
            my_index + 1,
            my_index + 3,
            my_index + 4,
            my_index + 5,
        ]
    )
    # print(f"candidate_indices: {candidate_indices}")
    if row == 0:
        candidate_indices.discard(my_index - 5)
        candidate_indices.discard(my_index - 4)
        candidate_indices.discard(my_index - 3)
    if row == 4:
        candidate_indices.discard(my_index + 5)
        candidate_indices.discard(my_index + 4)
        candidate_indices.discard(my_index + 3)
    if column == 0:
        candidate_indices.discard(my_index - 5)
        candidate_indices.discard(my_index - 1)
        candidate_indices.discard(my_index + 3)
    if column == 3:
        candidate_indices.discard(my_index - 3)
        candidate_indices.discard(my_index + 1)
        candidate_indices.discard(my_index + 5)
    neighbors = []
    for index in candidate_indices:
        if index >= 0 and index < len(all_suspects):
            neighbors.append(all_suspects[index])
    return neighbors


def count_innocent(suspects: list[str], hypothesis: dict[str, bool]) -> int:
    return sum(1 for suspect in suspects if hypothesis.get(suspect) == INNOCENT)


def count_criminal(suspects: list[str], hypothesis: dict[str, bool]) -> int:
    return sum(1 for suspect in suspects if hypothesis.get(suspect) == CRIMINAL)


def odd_criminals_column_a(suspects: set[str]) -> bool:
    column_a = [
        "Alex",
        "Freya",
        "Janet",
        "Nicole",
        "Uma",
    ]
    num_criminals = sum(
        1 for neighbor in column_a if suspects.get(neighbor) == CRIMINAL
    )
    return num_criminals // 2 == 1


def one_innocent_left_of_mark(suspects: set[str]) -> bool:
    left_of_mark = ["Janet", "Kay", "Lucy"]
    left_of_mark_innocent = sum(
        1 for neighbor in left_of_mark if suspects.get(neighbor) == INNOCENT
    )
    return left_of_mark_innocent == 1


def four_innocents_on_edges(suspects: set[str]) -> bool:
    edges = [
        "Alex",
        "Chad",
        "Daniel",
        "Eric",
        "Freya",
        "Isaac",
        "Janet",
        "Mark",
        "Nicole",
        "Terry",
        "Uma",
        "Vera",
        "Xia",
        "Ziad",
    ]
    rose_edge_neighbors = ["Janet", "Nicole", "Uma", "Vera", "Xia"]
    edge_innocent = sum(1 for neighbor in edges if suspects.get(neighbor) == INNOCENT)
    rose_edge_innocent = sum(
        1 for neighbor in rose_edge_neighbors if suspects.get(neighbor) == INNOCENT
    )
    return edge_innocent == 4 and rose_edge_innocent == 2


def only_one_row_has_exactly_two_innocents(suspects: set[str]) -> bool:
    rows = [
        ["Alex", "Chad"],
        ["Freya", "Gus"],
        ["Lucy", "Mark"],
        ["Nicole", "Rose", "Terry"],
        ["Uma", "Vera", "Xia", "Ziad"],
    ]
    innocents_by_row = [
        sum(1 for neighbor in row if suspects.get(neighbor) == INNOCENT) for row in rows
    ]
    return innocents_by_row.count(2) == 1


def find_commonalities(lineups: list[dict[str, bool]]) -> dict[str, bool]:
    if lineups == []:
        return {}
    commonalities = lineups[0].copy()
    for lineup in lineups[1:]:
        commonalities = {k: v for k, v in commonalities.items() if v == lineup.get(k)}
    return commonalities


def combine_rules_from_matrix(
    list_of_lists_of_dicts: list[list[dict[str, bool]]],
) -> set[frozenset[tuple[str, bool]]]:
    set_of_dicts = {frozenset(d.items()) for d in list_of_lists_of_dicts[0]}
    for list_of_dicts in list_of_lists_of_dicts:
        another_set_of_dicts = {frozenset(d.items()) for d in list_of_dicts}
        set_of_dicts = set_of_dicts.intersection(another_set_of_dicts)
    return set_of_dicts


def make_puzzle50() -> Puzzle:
    puzzle50 = Puzzle(
        suspects=[
            "Alex",
            "Chad",
            "Daniel",
            "Eric",
            "Freya",
            "Gus",
            "Hank",
            "Isaac",
            "Janet",
            "Kay",
            "Lucy",
            "Mark",
            "Nicole",
            "Rose",
            "Susan",
            "Terry",
            "Uma",
            "Vera",
            "Xia",
            "Ziad",
        ],
        known={
            "Lucy": INNOCENT,
            "Daniel": CRIMINAL,
            "Eric": CRIMINAL,
            "Janet": CRIMINAL,
            "Kay": CRIMINAL,
            "Susan": CRIMINAL,
            "Isaac": CRIMINAL,
            "Hank": CRIMINAL,
            # "Rose": CRIMINAL,
            # "Freya": CRIMINAL,
            # "Mark": CRIMINAL,
            # "Chad": INNOCENT,
            # "Terry": CRIMINAL,
            # "Xia": CRIMINAL,
            # "Nicole": INNOCENT,
        },
    )
    # print(f"neighbors of Rose: {puzzle50.get_neighbors('Rose')}")
    puzzle50.add_rule(
        "Daniel",
        lambda hypothesis: count_innocent(puzzle50.get_neighbors("Rose"), hypothesis)
        // 2
        == 1,
    )
    puzzle50.add_rule("Eric", one_innocent_left_of_mark)
    puzzle50.add_rule(
        "Janet",
        lambda hypothesis: count_innocent(puzzle50.get_neighbors("Xia"), hypothesis)
        == count_innocent(puzzle50.get_neighbors("Chad"), hypothesis),
    )
    puzzle50.add_rule("Kay", four_innocents_on_edges)
    puzzle50.add_rule(
        "Susan",
        lambda hypothesis: count_criminal(puzzle50.get_neighbors("Eric"), hypothesis)
        == count_criminal(puzzle50.get_neighbors("Freya"), hypothesis),
    )
    puzzle50.add_rule("Hank", only_one_row_has_exactly_two_innocents)
    return puzzle50


def make_puzzle49() -> Puzzle:
    puzzle49 = Puzzle(
        suspects=[
            "Andre",
            "Bruce",
            "Chuck",
            "Donna",
            "Erwin",
            "Freya",
            "Hank",
            "Isaac",
            "Janet",
            "Laura",
            "Nicole",
            "Oscar",
            "Paul",
            "Ruth",
            "Sarah",
            "Uma",
            "Vicky",
            "Will",
            "Xia",
            "Zach",
        ],
        known={},
    )

    def sarah2(hypothesis: dict[str, bool]) -> bool:
        # This is terrible. We'd like to terminate after finding a failure but that breaks how relevant_suspects works. So we need to reengineer relevant_suspects to make this more efficient.
        success = True
        for suspect in puzzle49.suspects:
            if suspect != "Andre":
                if count_innocent(puzzle49.get_neighbors(suspect), hypothesis) == 0:
                    # print(f"{suspect} has no innocent neighbors")
                    success = False
        return success

    puzzle49.add_rule(
        "Sarah",
        INNOCENT,
        sarah2,
    )
    puzzle49.add_rule(
        "Bruce",
        CRIMINAL,
        lambda hypothesis: (
            count_innocent(puzzle49.get_neighbors("Sarah"), hypothesis) == 3
        )
        and (count_innocent(["Ruth", "Uma"], hypothesis) == 1),
    )
    puzzle49.add_rule(
        "Erwin",
        CRIMINAL,
        lambda hypothesis: (
            count_innocent(puzzle49.get_neighbors("Will"), hypothesis) == 3
        )
        and (count_innocent(["Sarah", "Xia"], hypothesis) == 2),
    )
    puzzle49.add_rule(
        "Freya",
        CRIMINAL,
        lambda hypothesis: count_criminal(puzzle49.get_neighbors("Isaac"), hypothesis)
        % 2
        == 1,
    )
    puzzle49.add_rule(
        "Xia",
        INNOCENT,
        lambda hypothesis: count_innocent(
            ["Donna", "Isaac", "Oscar", "Uma", "Zach"], hypothesis
        )
        == 2,
    )
    puzzle49.add_rule(
        "Vicky",
        CRIMINAL,
        lambda hypothesis: count_criminal(puzzle49.get_neighbors("Isaac"), hypothesis)
        > count_criminal(puzzle49.get_neighbors("Xia"), hypothesis),
    )
    puzzle49.known["Nicole"] = CRIMINAL
    puzzle49.equal_criminal_neighbors(
        "Oscar",
        CRIMINAL,
        "Will",
        "Donna",
    )
    puzzle49.equal_innocent_neighbors(
        "Laura",
        CRIMINAL,
        "Zach",
        "Freya",
    )
    puzzle49.add_rule(
        "Donna",
        INNOCENT,
        lambda hypothesis: count_innocent(puzzle49.get_neighbors("Vicky"), hypothesis)
        % 2
        == 1,
    )
    puzzle49.known["Will"] = CRIMINAL
    puzzle49.known["Zach"] = INNOCENT
    puzzle49.known["Isaac"] = CRIMINAL
    puzzle49.known["Uma"] = CRIMINAL
    puzzle49.add_rule(
        "Ruth",
        INNOCENT,
        lambda hypothesis: count_criminal(puzzle49.get_neighbors("Bruce"), hypothesis)
        % 2
        == 1,
    )
    puzzle49.known["Paul"] = CRIMINAL
    puzzle49.known["Andre"] = INNOCENT

    puzzle49.add_rule(
        "Janet",
        CRIMINAL,
        lambda hypothesis: count_criminal(
            ["Hank", "Nicole", "Sarah", "Xia"], hypothesis
        )
        == 2,
    )
    puzzle49.criminals_connected("Janet2", None, ["Hank", "Nicole", "Sarah", "Xia"])
    return puzzle49


def make_puzzle48() -> Puzzle:
    puzzle48 = Puzzle(
        suspects=[
            "Amy",
            "Betty",
            "Chris",
            "Flora",
            "Gabe",
            "Hilda",
            "Isaac",
            "Karen",
            "Luigi",
            "Mary",
            "Nick",
            "Ollie",
            "Paula",
            "Ryan",
            "Stella",
            "Uma",
            "Vince",
            "Wanda",
            "Xavi",
            "Ziad",
        ],
        known={"Uma": INNOCENT},
    )
    puzzle48.add_rule(
        "Paula",
        CRIMINAL,
        lambda hypothesis: count_innocent(
            puzzle48.get_common_neighbors(["Hilda", "Mary"]), hypothesis
        )
        == 1,
    )

    row_2 = ["Gabe", "Hilda", "Isaac", "Karen"]
    puzzle48.add_rule(
        "Vince", CRIMINAL, lambda hypothesis: count_criminal(row_2, hypothesis) == 2
    )
    puzzle48.criminals_connected("Vince2", None, row_2)
    puzzle48.add_rule(
        "Luigi",
        CRIMINAL,
        lambda hypothesis: count_innocent(["Betty", "Flora", "Karen"], hypothesis) % 2
        == 1,
    )
    puzzle48.add_rule(
        "Nick",
        CRIMINAL,
        lambda hypothesis: count_innocent(
            ["Betty", "Hilda", "Mary", "Ryan"], hypothesis
        )
        == 2,
    )
    puzzle48.add_rule(
        "Nick2",
        None,
        lambda hypothesis: count_innocent(["Mary", "Ryan"], hypothesis) == 1,
    )
    puzzle48.add_rule(
        "Flora",
        INNOCENT,
        lambda hypothesis: count_innocent(puzzle48.get_neighbors("Nick"), hypothesis)
        == 4,
    )

    def flora2(hypothesis: dict[str, bool]) -> bool:
        # This is terrible. We'd like to terminate after finding a failure but that breaks how relevant_suspects works. So we need to reengineer relevant_suspects to make this more efficient.
        success = True
        for suspect in puzzle48.suspects:
            if suspect != "Nick":
                if count_innocent(puzzle48.get_neighbors(suspect), hypothesis) == 4:
                    success = False
        return success

    puzzle48.add_rule(
        "Flora2",
        None,
        flora2,
    )
    puzzle48.more_criminal_neighbors("Isaac", CRIMINAL, "Vince", "Flora")

    puzzle48.add_rule(
        "Gabe",
        INNOCENT,
        lambda hypothesis: count_innocent(puzzle48.get_neighbors("Isaac"), hypothesis)
        == 5,
    )

    # def gabe2(hypothesis: dict[str, bool]) -> bool:
    #     # This is terrible. We'd like to terminate after finding a failure but that breaks how relevant_suspects works. So we need to reengineer relevant_suspects to make this more efficient.
    #     success = True
    #     for suspect in puzzle48.suspects:
    #         if suspect != "Luigi":
    #             if count_innocent(puzzle48.get_neighbors(suspect), hypothesis) == 5:
    #                 success = False
    #     return success

    # puzzle48.add_rule(
    #     "Gabe2",
    #     None,
    #     gabe2,
    # )

    return puzzle48


def main() -> None:
    print("Away we go...")
    make_puzzle48().solve()


if __name__ == "__main__":
    main()
