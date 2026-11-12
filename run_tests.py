"""Standalone Test Runner executing unit and integration tests.

Executes tests using Python's standard library to guarantee instant execution
independent of external third-party package installation states.
"""
import sys
import unittest

def run():
    print("=" * 70)
    print("SMOG WATCH PAKISTAN - AUTOMATED TEST SUITE")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Load unit tests from src and test modules
    from src.aqi_calculator import calculate_sub_aqi, calculate_overall_aqi, get_aqi_category
    from src.ranking import rank_cities, calculate_national_summary
    from src.config import PRIMARY_FIVE_CITIES, PAKISTAN_CITIES

    class StandardAQITests(unittest.TestCase):
        def test_pm25_boundary_values(self):
            self.assertEqual(calculate_sub_aqi("pm2_5", 0.0), 0)
            self.assertEqual(calculate_sub_aqi("pm2_5", 12.0), 50)
            self.assertEqual(calculate_sub_aqi("pm2_5", 35.4), 100)
            self.assertEqual(calculate_sub_aqi("pm2_5", 55.4), 150)
            self.assertEqual(calculate_sub_aqi("pm2_5", 150.4), 200)
            self.assertEqual(calculate_sub_aqi("pm2_5", 250.4), 300)
            self.assertEqual(calculate_sub_aqi("pm2_5", 350.4), 400)
            self.assertEqual(calculate_sub_aqi("pm2_5", 500.4), 500)

        def test_pm25_interpolation(self):
            aqi = calculate_sub_aqi("pm2_5", 25.0)
            self.assertTrue(51 <= aqi <= 100)
            aqi_high = calculate_sub_aqi("pm2_5", 100.0)
            self.assertTrue(151 <= aqi_high <= 200)

        def test_pm10_boundary_values(self):
            self.assertEqual(calculate_sub_aqi("pm10", 0.0), 0)
            self.assertEqual(calculate_sub_aqi("pm10", 54.0), 50)
            self.assertEqual(calculate_sub_aqi("pm10", 154.0), 100)
            self.assertEqual(calculate_sub_aqi("pm10", 254.0), 150)
            self.assertEqual(calculate_sub_aqi("pm10", 354.0), 200)
            self.assertEqual(calculate_sub_aqi("pm10", 424.0), 300)
            self.assertEqual(calculate_sub_aqi("pm10", 504.0), 400)
            self.assertEqual(calculate_sub_aqi("pm10", 604.0), 500)

        def test_zero_fabrication_on_missing(self):
            self.assertIsNone(calculate_sub_aqi("pm2_5", None))
            self.assertIsNone(calculate_sub_aqi("pm2_5", float("nan")))
            self.assertIsNone(calculate_sub_aqi("pm2_5", -5.0))
            self.assertIsNone(calculate_sub_aqi("pm2_5", "not_a_number"))

        def test_composite_overall_aqi(self):
            # Dominant PM2.5
            res1 = calculate_overall_aqi({"pm2_5": 60.0, "pm10": 40.0})
            self.assertEqual(res1["status"], "valid")
            self.assertEqual(res1["responsible_pollutant"], "pm2_5")

            # Dominant PM10
            res2 = calculate_overall_aqi({"pm2_5": 10.0, "pm10": 200.0})
            self.assertEqual(res2["status"], "valid")
            self.assertEqual(res2["responsible_pollutant"], "pm10")

            # All missing
            res3 = calculate_overall_aqi({"pm2_5": None, "pm10": None})
            self.assertEqual(res3["status"], "insufficient_data")
            self.assertIsNone(res3["aqi"])
            self.assertEqual(res3["category"]["name"], "Data Unavailable")

        def test_aqi_categories(self):
            self.assertEqual(get_aqi_category(30)["name"], "Good")
            self.assertEqual(get_aqi_category(80)["name"], "Moderate")
            self.assertEqual(get_aqi_category(130)["name"], "Unhealthy for Sensitive Groups")
            self.assertEqual(get_aqi_category(180)["name"], "Unhealthy")
            self.assertEqual(get_aqi_category(250)["name"], "Very Unhealthy")
            self.assertEqual(get_aqi_category(350)["name"], "Hazardous")
            self.assertEqual(get_aqi_category(None)["name"], "Data Unavailable")

    class StandardRankingTests(unittest.TestCase):
        def test_ranking_order(self):
            data = {
                "City1": {"status": "success", "aqi": 180, "pollutants": {"pm2_5": 80.0}},
                "City2": {"status": "success", "aqi": 310, "pollutants": {"pm2_5": 160.0}},
                "City3": {"status": "success", "aqi": 95, "pollutants": {"pm2_5": 30.0}}
            }
            ranked = rank_cities(data)
            self.assertEqual(ranked[0]["city"], "City2")
            self.assertEqual(ranked[0]["rank"], 1)
            self.assertEqual(ranked[1]["city"], "City1")
            self.assertEqual(ranked[1]["rank"], 2)
            self.assertEqual(ranked[2]["city"], "City3")
            self.assertEqual(ranked[2]["rank"], 3)

        def test_tie_breaking(self):
            data = {
                "CityA": {"status": "success", "aqi": 150, "pollutants": {"pm2_5": 50.0}},
                "CityB": {"status": "success", "aqi": 150, "pollutants": {"pm2_5": 55.0}}
            }
            ranked = rank_cities(data)
            self.assertEqual(ranked[0]["city"], "CityB")
            self.assertEqual(ranked[1]["city"], "CityA")

        def test_unreachable_stations(self):
            data = {
                "Lahore": {"status": "success", "aqi": 210, "pollutants": {"pm2_5": 90.0}},
                "Peshawar": {"status": "error", "aqi": None, "pollutants": {}, "error_message": "Timeout"}
            }
            ranked = rank_cities(data)
            self.assertEqual(ranked[0]["city"], "Lahore")
            self.assertEqual(ranked[0]["rank"], 1)
            self.assertEqual(ranked[1]["city"], "Peshawar")
            self.assertIsNone(ranked[1]["rank"])
            self.assertEqual(ranked[1]["rank_display"], "—")
            self.assertFalse(ranked[1]["is_reporting"])

        def test_national_summary(self):
            data = {
                "City1": {"status": "success", "aqi": 300, "pollutants": {"pm2_5": 150.0}},
                "City2": {"status": "success", "aqi": 100, "pollutants": {"pm2_5": 35.0}},
                "City3": {"status": "error", "aqi": None, "pollutants": {}}
            }
            ranked = rank_cities(data)
            summary = calculate_national_summary(ranked)
            self.assertEqual(summary["reporting_count"], 2)
            self.assertEqual(summary["total_stations"], 3)
            self.assertEqual(summary["average_aqi"], 200.0)
            self.assertEqual(summary["worst_city"], "City1")
            self.assertEqual(summary["cleanest_city"], "City2")

    class PakistaniCitiesComplianceTests(unittest.TestCase):
        def test_all_five_cities_configured(self):
            expected = {"Lahore", "Karachi", "Islamabad", "Faisalabad", "Peshawar"}
            self.assertEqual(set(PRIMARY_FIVE_CITIES), expected)

            for city in expected:
                self.assertIn(city, PAKISTAN_CITIES)
                meta = PAKISTAN_CITIES[city]
                self.assertTrue(meta["is_primary"])
                self.assertTrue(23.0 <= meta["latitude"] <= 37.5)
                self.assertTrue(60.0 <= meta["longitude"] <= 78.5)

    suite.addTest(loader.loadTestsFromTestCase(StandardAQITests))
    suite.addTest(loader.loadTestsFromTestCase(StandardRankingTests))
    suite.addTest(loader.loadTestsFromTestCase(PakistaniCitiesComplianceTests))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == "__main__":
    run()
