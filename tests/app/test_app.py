import unittest
import os
from tests.config.definitions import ROOT_DIR
from app.app import App
from sdk.moveapps_io import MoveAppsIo
import pandas as pd
import random

print("Conducting unit tests. ")

class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        os.environ['APP_ARTIFACTS_DIR'] = os.path.join(ROOT_DIR, 'tests/resources/output')
        self.sut = App(moveapps_io=MoveAppsIo())  

    #Checks the input file compared to the output after it was run
    def test_app_returns_input(self):
        # prepare
        expected = pd.read_pickle("./resources/samples/martesAllNY.pickle")

        #config: dict = {}
        config: dict = {"keys": "Key-Pair-Id=APKAIDPUN4QMG7VUQPSA&Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6Imh0dHBzOi8vaGVhdG1hcC1leHRlcm5hbC0qLnN0cmF2YS5jb20vKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTY4NTcyOTQyOH0sIkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNjg0NTA1NDI4fX19XX0_&Signature=hJFIxHJuYXQW0XiqaeBCqy6dKU79BYRRNKr-y6bVgYBaO1Z9horGitL2T4fBi7nCQv3Q89VRhQ0TSYrQg4lsIjVntz7YGCFE3d8O3VFrB3KaI7ghY-NIqxF~S8SN5hf7uM8F0bOjTiqTcj02dLkcNXYtJ3Rt7gjDGklqEInengOIQACYxcbKdT3AUwKb5LfcUDUHRuo-wp49lRoKK0Gbcq55i~4uCU4WjO3K2M9a-PkO465bY7qNii2JI~nu4qezCgogoeaQaVAdMM46ucSv5cmN3CdEoc4sUPKcWR8FCxNtbbjmFg7w8AT1~v6XzU0KecKjMdZG8athHblHo7tcow__"}

        # execute
        actual = self.sut.execute(data=expected, config=config)

        #verify
        expectedList = []
        actualList = []
        expectedLength = len(expected.to_point_gdf())
        actualLength = len(actual.to_point_gdf())
        expectedGdf = expected.to_point_gdf()
        actualGdf = actual.to_point_gdf()
        actCols = len(actualGdf.iloc[0])
        expectedList.append(expectedGdf.iloc[expectedLength-1][0])
        actualList.append(actualGdf.iloc[actualLength-1][0])

        #checks a 500 column row coordinates at random within the dataset excluding the 7 columns that I have changed or added inlcuding point, distance, intensity, geometry, band 1, band 2, band 3, and band 4
        for i in range(500):
            randRow = random.randint(0, actualLength - 1)
            randCol = random.randint(0, actCols - 8)
            if pd.isna(actualGdf.iloc[randRow][randCol]):
                continue
            else:
                expectedList.append(expectedGdf.iloc[randRow][randCol])
                actualList.append(actualGdf.iloc[randRow][randCol]) 

        #check the list
        self.assertListEqual(expectedList, actualList)

        #geometries should be unequal between the expected and actual
        self.assertNotEqual(expectedGdf.iloc[actualLength-1][actCols-7], actualGdf.iloc[actualLength-1][actCols-7])
        
if __name__ == '__main__':
    unittest.main()