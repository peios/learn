export function normalize(value: number): number {
    if (value < 0) return 0;
    return value;
}

export const FIELD_NAMES = [
    "legacy_name",
    "another_name_that_makes_this_list_long_enough_to_need_more_than_one_line",
    "final_name",
];
