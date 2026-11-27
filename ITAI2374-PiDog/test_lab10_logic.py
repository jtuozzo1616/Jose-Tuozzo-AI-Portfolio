#!/usr/bin/env python3
"""Hardware-independent unit tests for Lab 10 sensor-fusion logic."""
import unittest
from lab10_multisensor import (
    clean_distance, marker_side, sound_side, choose_avoidance,
)


class FusionLogicTests(unittest.TestCase):
    def test_invalid_distances_fail_closed(self):
        for value in [-1, 0, None, 500, float('nan'), 'bad']:
            self.assertIsNone(clean_distance(value))
        self.assertEqual(clean_distance('27.5'), 27.5)

    def test_vision_direction(self):
        self.assertEqual(marker_side(30, 1000), 'left')
        self.assertEqual(marker_side(160, 1000), 'center')
        self.assertEqual(marker_side(300, 1000), 'right')
        self.assertIsNone(marker_side(30, 10))

    def test_sound_bearing(self):
        self.assertEqual(sound_side(90), 'right')
        self.assertEqual(sound_side(270), 'left')
        self.assertIsNone(sound_side(0))

    def test_reject_both_blocked(self):
        self.assertIsNone(choose_avoidance(20, 31, 'right', 'right'))

    def test_clearest_side_is_preferred(self):
        self.assertEqual(choose_avoidance(90, 45, None, None), 'left')

    def test_vision_can_bias_safe_route(self):
        self.assertEqual(choose_avoidance(52, 50, 'right', None), 'right')

    def test_vision_cannot_override_unsafe_sonar(self):
        self.assertEqual(choose_avoidance(60, 30, 'right', 'right'), 'left')

    def test_audio_used_only_when_vision_absent(self):
        self.assertEqual(choose_avoidance(50, 50, None, 'right'), 'right')
        self.assertEqual(choose_avoidance(50, 50, 'left', 'right'), 'left')


if __name__ == '__main__':
    unittest.main(verbosity=2)
