"""Explicit source boundary for the academic experiment reset."""

SOURCE_TABLES = frozenset({
    'academic_source_files',
    'academic_reference_rows',
    'academic_data_dictionary',
    'academic_simulation_snapshots',
    'model_training_observations',
})


def partition_tables(names):
    names = set(names)
    if not SOURCE_TABLES <= names:
        raise ValueError('Academic source schema incomplete; migrate before resetting experiments')
    return sorted(SOURCE_TABLES), sorted(names - SOURCE_TABLES)
