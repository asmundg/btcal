import arrow
from freezegun import freeze_time
from btcal import btcal


@freeze_time('2016-05-01')
def test_dateparser():
    assert btcal.event_datetime('\n 25. mai\n\n  \n  kl. 08:00\n   ') == [
        arrow.get('2016-05-25T06:00:00Z'), arrow.get('2016-05-25T06:00:00Z')]
    assert btcal.event_datetime('\n 1. januar\n\n  \n  kl. 08:00 \n- 10:00\n') == [
        arrow.get('2017-01-01T07:00:00Z'), arrow.get('2017-01-01T09:00:00Z')]
