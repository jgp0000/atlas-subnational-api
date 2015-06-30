# vim: set fileencoding=utf8

import pandas as pd
import numpy as np


from atlas_core.helpers.data_import import translate_columns
from colombia import models, create_app
from colombia.core import db
from tests import BaseTestCase


def fillin(df, entities):
    """STATA style "fillin", make sure all permutations of entities in the
    index are in the dataset."""
    df = df.set_index(entities)
    return df.reindex(
        pd.MultiIndex.from_product(df.index.levels, names=df.index.names))


def cut_columns(df, columns):
    return df[list(columns)]

# Classification.merge_to_table
# Classification.merge_index
def merge_to_table(classification, classification_name, df, merge_on):
    code_to_id = classification.reset_index()[["code", "index"]]
    code_to_id.columns = ["code", classification_name]
    code_to_id = code_to_id.set_index("code")
    return df.merge(code_to_id, left_on=merge_on,
                    right_index=True, how="left")


def classification_to_models(classification, model):
    models = []
    for index, row in classification.table.iterrows():
        row = row.replace([np.nan], [None])
        m = model()
        m.id = index.item()
        m.code = row["code"]
        m.name_en = row["name"]
        m.level = row["level"]
        m.parent_id = row["parent_id"]
        models.append(m)
    return models

aduanas_to_atlas = {
    "r": "department",
    "p": "product",
    "yr": "year",
    "X_rpy_p": "export_value",
    "density_natl": "density",
    "eci_natl": "eci",
    "pci": "pci",
    "coi_natl": "coi",
    "cog_natl": "cog",
    "RCA_natl": "export_rca"
}

gdp_to_atlas = {
    "depcode": "department",
    "depgdpn": "gdp_nominal",
    "gdpkmultipliedbydeflator": "gdp_real",
    "year": "year"
}


pop_to_atlas = {
    "year": "year",
    "dp": "department",
    "popdept": "population"
}

pila_to_atlas = {
    "r": "department",
    "i": "industry",
    "year": "year",
    "E_yir": "employment",
    "W_yir": "wages",
    "rca": "rca",
    "density": "density",
    "cog": "cog",
    "coi": "coi",
    "pci": "complexity"
}

pila_to_atlas_muni = dict(pila_to_atlas.items())
pila_to_atlas_muni["r"] = "municipality"


class ImporterTestCase(BaseTestCase):

    SQLALCHEMY_DATABASE_URI = "sqlite://"

    def test_translate_columns(self):

        randomdata = pd.DataFrame(np.random.randn(6, 4),
                                  columns=list('abcd'))

        translation_table = {"a": "x", "b": "y", "c": "z"}
        translated = translate_columns(
            randomdata,
            translation_table
        )

        self.assertEquals(3, len(translated.columns))
        self.assertIn("x", translated.columns)
        self.assertIn("y", translated.columns)
        self.assertIn("z", translated.columns)
        self.assertNotIn("a", translated.columns)
        self.assertNotIn("b", translated.columns)
        self.assertNotIn("c", translated.columns)
        self.assertNotIn("d", translated.columns)

    def test_process_cpy(self):

        # Pass in a CPY and an ecomplexity file
        # Get import / export from CPY
        # Get CY / PY from ecomplexity


        department_map = {
            "10": models.Department(code="10", name="foo"),
        }

        product_map = {
            "22": models.HSProduct(code="22", name="Cars"),
            "24": models.HSProduct(code="24", name="Cars"),
        }

        db.session.add_all(department_map.values())
        db.session.add_all(product_map.values())
        db.session.commit()

        data = [
            {"department": "10", "product": "22", "year": 1998, "export_value": 1234,
             "density": 1, "eci": 4, "pci": 3, "diversity": 1, "ubiquity": 1,
             "coi": 1, "cog": 1, "export_rca": 1, "import_value": 22},
            {"department": "10", "product": "24", "year": 1998, "export_value": 4321,
             "density": 1, "eci": 4, "pci": 1, "diversity": 1, "ubiquity": 1,
             "coi": 1, "cog": 1, "export_rca": 1, "import_value": 44},
            {"department": "10", "product": "22", "year": 1999, "export_value": 9999,
             "density": 1, "eci": 7, "pci": 3, "diversity": 1, "ubiquity": 1,
             "coi": 1, "cog": 1, "export_rca": 1, "import_value": 666},
        ]
        data = pd.DataFrame.from_dict(data)

        # CPY
        cy, py, cpy = process_cpy(data, product_map, department_map)

        db.session.add_all(cy)
        db.session.add_all(py)
        db.session.add_all(cpy)
        db.session.commit()

        # TODO imports
        # TODO distance vs density

        len(cpy) == 3  # cpy: export, rca, density, cog, coi
        self.assertEquals(cpy[0].export_value, 1234)
        self.assertEquals(cpy[0].export_rca, 1)
        self.assertEquals(cpy[0].density, 1)
        self.assertEquals(cpy[0].cog, 1)
        self.assertEquals(cpy[0].coi, 1)
        self.assertEquals(cpy[0].year, 1998)
        self.assertEquals(cpy[0].department, department_map["10"])
        self.assertEquals(cpy[0].product, product_map["22"])
        self.assertEquals(cpy[1].export_value, 4321)
        self.assertEquals(cpy[1].import_value, 44)
        self.assertEquals(cpy[1].export_rca, 1)
        self.assertEquals(cpy[1].density, 1)
        self.assertEquals(cpy[1].cog, 1)
        self.assertEquals(cpy[1].coi, 1)
        self.assertEquals(cpy[1].department, department_map["10"])
        self.assertEquals(cpy[1].product, product_map["24"])
        self.assertEquals(cpy[1].year, 1998)
        self.assertEquals(cpy[2].export_value, 9999)
        self.assertEquals(cpy[2].export_rca, 1)
        self.assertEquals(cpy[2].density, 1)
        self.assertEquals(cpy[2].cog, 1)
        self.assertEquals(cpy[2].coi, 1)
        self.assertEquals(cpy[2].year, 1999)
        self.assertEquals(cpy[2].department, department_map["10"])
        self.assertEquals(cpy[2].product, product_map["22"])

        # TODO eci_rank

        len(cy) == 2  # department, year, eci, eci_rank, diversity
        self.assertNotEquals(cy[0].department_id, 10)
        self.assertEquals(cy[0].department, department_map["10"])
        self.assertEquals(cy[0].year, 1998)
        self.assertEquals(cy[0].eci, 4)
        self.assertEquals(cy[0].diversity, 1)
        self.assertNotEquals(cy[1].department_id, 10)
        self.assertEquals(cy[1].department, department_map["10"])
        self.assertEquals(cy[1].year, 1999)
        self.assertEquals(cy[1].eci, 7)
        self.assertEquals(cy[1].diversity, 1)

        # TODO pci_rank

        len(py) == 3  # product, year, pci, pci_rank
        self.assertNotEquals(py[0].product_id, 22)
        self.assertEquals(py[0].product, product_map["22"])
        self.assertEquals(py[0].year, 1998)
        self.assertEquals(py[0].pci, 3)
        self.assertNotEquals(py[1].product_id, 22)
        self.assertEquals(py[1].product, product_map["22"])
        self.assertEquals(py[1].year, 1999)
        self.assertEquals(py[1].pci, 3)
        self.assertNotEquals(py[2].product_id, 24)
        self.assertEquals(py[2].product, product_map["24"])
        self.assertEquals(py[2].year, 1998)
        self.assertEquals(py[2].pci, 1)



if __name__ == "__main__":

        app = create_app()

        with app.app_context():

            # Load classifications
            from linnaeus import classification
            product_classification = classification.load("product/HS/Atlas/out/hs92_atlas.csv")
            products = classification_to_models(product_classification,
                                                models.HSProduct)
            db.session.add_all(products)
            db.session.commit()

            location_classification = classification.load("location/Colombia/DANE/out/locations_colombia_dane.csv")
            locations = classification_to_models(location_classification,
                                                models.Location)
            db.session.add_all(locations)
            db.session.commit()

            industry_classification = classification.load("industry/ISIC/Colombia/out/isic_ac_3.0.csv")
            industries = classification_to_models(industry_classification,
                                                  models.Industry)
            db.session.add_all(industries)
            db.session.commit()

            # Department product year
            df = pd.read_stata("/Users/makmana/ciddata/Aduanas/exp_ecomplexity_dpto_oldstata.dta")
            df = translate_columns(df, aduanas_to_atlas)
            df = cut_columns(df, aduanas_to_atlas.values())
            df["product"] = df["product"].astype(int).astype(str).str.zfill(4)

            # Cleaning notes
            # ==============
            # Fix column names
            # Cut columns
            # Fix types

            # Prefiltering

            # Rectangularize by facet fields? If this comes from classification, do this later
            # Fill digit numbers on classification fields if necessary
            # Merge classification fields, convert from code to ID

            # Group by entities to get facets
            # Aggregate each facets
            # - eci / pci first()
            # - generate rank fields rank(method='dense')
            # - export_value sum()
            # Filterations on facets

            # Merge similar facet data (DY datasets together, etc)
            # Load merged facet to given model

            # Generate other cross-dataset columns: gdp per capita


            # Dataset:
            # - actual names to db names
            # - Which ones are entity fields
            # - numpy / db types of fields
            # - mappings to classification object
            # - field group + how to aggregate each data field in that group


            df = fillin(df, ["department", "product", "year"]).reset_index()

            df = merge_to_table(product_classification.level("4digit"),
                                "product_id", df, "product")
            df = merge_to_table(location_classification.level("department"),
                                "department_id", df, "department")


            py = df.groupby(["product_id", "year"])[["pci"]].first().reset_index()
            py.to_sql("product_year", db.engine, index=False,
                      chunksize=10000, if_exists="append")

            # GDP data
            gdp_df = pd.read_stata("/Users/makmana/ciddata/metadata/Annual GDP (nominal)/COL_nomrealgdp_dept_annual1990-2012.dta")
            gdp_df = translate_columns(gdp_df, gdp_to_atlas)
            gdp_df = cut_columns(gdp_df, gdp_to_atlas.values())

            gdp_df.gdp_real = gdp_df.gdp_real * (10 ** 6)
            gdp_df.gdp_nominal = gdp_df.gdp_nominal * (10 ** 6)
            gdp_df.department = gdp_df.department.astype(str).str.zfill(2)

            # Pop data
            pop_df = pd.read_stata("/Users/makmana/ciddata/metadata/Population/COL_pop_deptmunicip_1985-2012.dta")
            pop_df = translate_columns(pop_df, pop_to_atlas)
            pop_df = cut_columns(pop_df, pop_to_atlas.values())

            pop_df = pop_df.groupby(["department", "year"])[["population"]].first().reset_index()

            pop_df.department = pop_df.department.astype(str).str.zfill(2)
            pop_df = pop_df[(2007 <= pop_df.year) & (pop_df.year <= 2013)]

            cy = df.groupby(["department", "year"])[["eci", "department_id"]].first().reset_index()
            cy = cy.merge(gdp_df,
                          on=["department", "year"],
                          how="left")
            cy = cy.merge(pop_df,
                          on=["department", "year"],
                          how="left")
            cy["gdp_pc_real"] = cy.gdp_real / cy.population
            cy["gdp_pc_nominal"] = cy.gdp_nominal / cy.population

            # TODO: In the real thing, we won't need this "department" column
            # here because we won't need to merge based on code because
            # everything will have been converted to IDs already.
            cy = cy.drop("department", axis=1)
            cy.to_sql("department_year", db.engine, index=False,
                      chunksize=10000, if_exists="append")

            df = df.groupby(["department_id", "product_id", "year"])[["export_value", "export_rca", "density", "cog", "coi"]].first().reset_index()
            df.to_sql("department_product_year", db.engine, index=False,
                      chunksize=10000, if_exists="append")


            # Department - industry - year
            df = pd.read_stata("/Users/makmana/ciddata/PILA_andres/COL_PILA_ecomp-E_yir_2008-2012_rev3_dpto.dta")
            df = translate_columns(df, pila_to_atlas)
            df = cut_columns(df, pila_to_atlas.values())

            df = df[df.industry != "."]

            df = fillin(df, ["department", "industry", "year"]).reset_index()

            df = merge_to_table(industry_classification.level("class"),
                                "industry_id", df, "industry")
            df = merge_to_table(location_classification.level("department"),
                                "department_id", df, "department")

            # Industry - Year
            iy = df.groupby(["industry_id", "year"])[["complexity"]].first().reset_index()
            iy.to_sql("industry_year", db.engine, index=False,
                      chunksize=10000, if_exists="append")

            # Department - industry - year
            df = df.groupby(["department_id", "industry_id", "year"])[["employment", "wages", "rca", "density", "cog", "coi"]].first().reset_index()
            df.to_sql("department_industry_year", db.engine, index=False,
                      chunksize=10000, if_exists="append")


            # Municipality - industry - year
            df = pd.read_stata("/Users/makmana/ciddata/PILA_andres/COL_PILA_ecomp-E_yir_2008-2012_rev3_mun.dta")
            df = translate_columns(df, pila_to_atlas_muni)
            df = cut_columns(df, pila_to_atlas_muni.values())

            df = df[df.industry != "."]

            df = fillin(df, ["municipality", "industry", "year"]).reset_index()

            df = merge_to_table(industry_classification.level("class"),
                                "industry_id", df, "industry")
            df = merge_to_table(location_classification.level("municipality"),
                                "municipality_id", df, "municipality")

            df = df.groupby(["municipality_id", "industry_id", "year"])[["employment", "wages", "rca", "density", "cog", "coi"]].first().reset_index()
            df.to_sql("municipality_industry_year", db.engine, index=False,
                      chunksize=10000, if_exists="append")
