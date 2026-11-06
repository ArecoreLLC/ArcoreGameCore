"""Checks for attribution, units, unavailable counters, and first-token timing."""
import unittest

from vision_metrics import aggregate_engines,sample_stats,FirstTokenClock


class VisionMetricTests(unittest.TestCase):
    def test_gpu_engines_sum_processes_but_not_parallel_engines(self):
        items=[
            ('pid_10_luid_0x0_0x1_phys_0_eng_0_engtype_3D',20),
            ('pid_20_luid_0x0_0x1_phys_0_eng_0_engtype_3D',30),
            ('pid_10_luid_0x0_0x1_phys_0_eng_1_engtype_Compute',40),
            ('pid_20_luid_0x0_0x1_phys_0_eng_1_engtype_Compute',30),
        ]
        self.assertEqual(aggregate_engines(items,10),(70,40))
        self.assertEqual(aggregate_engines(items,99),(70,0))

    def test_missing_gpu_measurements_are_not_reported_as_idle(self):
        self.assertEqual(aggregate_engines([],10),(None,None))
        self.assertEqual(aggregate_engines([('invalid instance',99)],10),(None,None))
        self.assertEqual(sample_stats([{'gpu':None,'interval_seconds':1}],'gpu'),{'mean':None,'peak':None,'samples':0})

    def test_sample_mean_uses_elapsed_time_and_ignores_invalid_values(self):
        samples=[{'cpu':10,'interval_seconds':1},{'cpu':30,'interval_seconds':3},{'cpu':float('nan'),'interval_seconds':5}]
        self.assertEqual(sample_stats(samples,'cpu'),{'mean':25.0,'peak':30,'samples':2})

    def test_first_token_clock_excludes_the_prompt_and_retains_first_time(self):
        times=iter([10,10.125])
        timer=FirstTokenClock(clock=lambda:next(times))
        timer.put('prompt')
        self.assertIsNone(timer.first_token_seconds)
        timer.put('first generated token');timer.put('next token');timer.end()
        self.assertEqual(timer.first_token_seconds,.125)


if __name__=='__main__':
    unittest.main()
