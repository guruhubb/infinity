import models
import unittest
import pytz

from mongoengine import *
import models
import datetime


def get_capacity_estimate(snr, mcs, retransmit_percentage, number_of_cpes):
    table = [4.47, 8.5, 12.8, 17.0, 24.5, 37.3, 40, 40, 9.0, 17, 26, 34, 48, 55, 60, 60, 13.9, 26.2, 36.8, 48, 55, 60,
             60, 60, 18, 32, 44, 55, 60, 60, 60, 60
            ]

    mcs_low_snr = table[0]
    capacity_estimate = table[int(round(mcs))]

    if snr < 4:
        capacity_estimate += (snr / 1.2) - mcs_low_snr
        # app.logger.debug('capacity_estimate in snr < 4: %s, ' % capacity_estimate)

    if snr < 7:
        exponent = 2
    else:
        exponent = 1.2

    capacity_estimate *= (1-(retransmit_percentage/100.0))**exponent
    avg_capacity_estimate = capacity_estimate/number_of_cpes

    return avg_capacity_estimate


class ModelTestCase(unittest.TestCase):

    def setUp(self):
        connect(db='nms')

    def test_expectedcapacity(self):

        start_date = datetime.datetime(year=2014, month=8, day=28, hour=23, minute=06, second=00, tzinfo=pytz.utc)

        metric_cpe_snr = models.MetricDefinition.objects(name='CPE_SNR').first()
        metric_cpe_cms = models.MetricDefinition.objects(name='CPE_MCS').first()
        metric_bts_cms = models.MetricDefinition.objects(name='BTS_MCS').first()
        metric_bts_arq_retx_percent = models.MetricDefinition.objects(name='BTS_ARQ_RETX_PERCENT').first()
        metric_cpe_cap = models.MetricDefinition.objects(name='CPE_CAP').first()
        metric_cpe_rxtx = models.MetricDefinition.objects(name='CPE_RXTX').first()

        cpe_snr = float(models.MetricRecord.objects(metric_definition=metric_cpe_snr, time=start_date).first().values[0].value)
        cpe_mcs = float(models.MetricRecord.objects(metric_definition=metric_cpe_cms, time=start_date).first().values[0].value)
        bts_mcs = float(models.MetricRecord.objects(metric_definition=metric_bts_cms, time=start_date).first().values[0].value)
        bts_arq_retx_percent =float(models.MetricRecord.objects(metric_definition=metric_bts_arq_retx_percent, time=start_date).first().values[0].value)


        cpe_cap = models.MetricRecord.objects(metric_definition=metric_cpe_cap, time=start_date).first()
        cpe_rxtx = models.MetricRecord.objects(metric_definition=metric_cpe_rxtx, time=start_date).first()

        capacity_estimate = get_capacity_estimate(cpe_snr, bts_mcs, bts_arq_retx_percent, 1)


        print "cpacity_estimate  is: %f" % capacity_estimate

        # self.assertEqual(len(rels), 2)
        #
        # self.assertTrue(isinstance(rels[0].entity, models.Person))
        # self.assertTrue(isinstance(rels[1].entity, models.Organisation))


if __name__ == '__main__':
    unittest.main()