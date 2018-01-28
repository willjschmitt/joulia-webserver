import logging

LOGGER = logging.getLogger(__name__)


def add_hop_ingredients(apps, _):
    """Adds malt ingredients from malt_ingredients.tsv into the MaltIngredient
    database. If an ingredient already exists with the provided name, it will
    skip it.
    """
    BitteringIngredient = apps.get_model('brewery', 'BitteringIngredient')
    with open('brewery/migrations/hop_ingredients.tsv') as ingredient_file:
        for row in ingredient_file:
            try:
                if row[0] == '#':
                    LOGGER.info(row)
                    continue
                name, alpha_acid_percent_string = row.split('\t')
                if BitteringIngredient.objects.filter(name=name).exists():
                    LOGGER.warning('%s already exists in database. Skipping.',
                                   name)
                    continue
                alpha_acid_percent = float(alpha_acid_percent_string)
                alpha_acid_weight = alpha_acid_percent / 100.0
                BitteringIngredient.objects.create(
                    name=name, alpha_acid_weight=alpha_acid_weight)
            except Exception as e:
                raise Exception("In " + row + ": " + e.args[0])