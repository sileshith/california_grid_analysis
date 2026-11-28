"""Download and validate seasonal OASIS reports with conservative pacing."""
import csv
import hashlib
import io
import json
import time
import zipfile
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'verification/oasis_download_requests.json'


def validate(data, request):
    start = datetime.strptime(request['startdatetime'], '%Y%m%dT%H:%M-0000').replace(tzinfo=timezone.utc)
    end = datetime.strptime(request['enddatetime'], '%Y%m%dT%H:%M-0000').replace(tzinfo=timezone.utc)
    market = request['market_run_id']
    item = 'SYS_FCST_DA_MW' if market == 'DAM' else 'SYS_FCST_ACT_MW'
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        if len(names) != 1 or not names[0].lower().endswith('.csv'):
            raise ValueError('Expected one CSV report, received ' + repr(names))
        rows = list(csv.DictReader(io.StringIO(archive.read(names[0]).decode('utf-8-sig'))))
    if not rows or not all(r['MARKET_RUN_ID'] == market and r['XML_DATA_ITEM'] == item for r in rows):
        raise ValueError('Wrong report item or market')
    selected = [r for r in rows if r['TAC_AREA_NAME'] == 'CA ISO-TAC']
    times = []
    for row in selected:
        t = datetime.fromisoformat(row['INTERVALSTARTTIME_GMT'])
        e = datetime.fromisoformat(row['INTERVALENDTIME_GMT'])
        if e-t != timedelta(hours=1) or not start <= t < end:
            raise ValueError('Unexpected interval timestamps')
        if not __import__('math').isfinite(float(row['MW'])):
            raise ValueError('Nonfinite demand')
        times.append(t)
    expected = {start + timedelta(hours=h) for h in range(int((end-start).total_seconds()/3600))}
    if set(times) != expected or len(times) != len(expected):
        raise ValueError(f'Coverage mismatch: {len(times)} rows, {len(set(times))} unique, {len(expected)} required')
    return dict(valid=True, area='CA ISO-TAC', hours=len(times), item=item, member=names[0])


def main():
    requests = json.loads(MANIFEST.read_text())
    last_request = 0.0
    next_allowed = 0.0
    for request in requests:
        path = ROOT / request['target']
        params = {k:request[k] for k in ['queryname','startdatetime','enddatetime','version','market_run_id','resultformat']}
        request['url'] = 'https://oasis.caiso.com/oasisapi/SingleZip?' + urlencode(params)
        request.setdefault('attempts', [])
        if path.exists():
            request['validation'] = validate(path.read_bytes(), request)
            request['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            request['downloaded'] = True
            MANIFEST.write_text(json.dumps(requests, indent=2)+'\n')
            print('KEPT', request['target'], flush=True)
            continue
        for attempt in range(1, 4):
            wait = max(last_request+60, next_allowed)-time.time()
            while wait > 0:
                time.sleep(min(wait, 30))
                wait = max(last_request+60, next_allowed)-time.time()
            last_request = time.time()
            record = dict(attempt=attempt, requested_at=datetime.now(timezone.utc).isoformat())
            try:
                with urlopen(request['url'], timeout=45) as response:
                    data = response.read()
                    record['http_status'] = response.status
                    validation = validate(data, request)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                request.update(downloaded=True, validation=validation, sha256=hashlib.sha256(data).hexdigest())
                record['outcome'] = 'validated'
            except Exception as error:
                record.update(outcome='failed', error=f'{type(error).__name__}: {error}')
                if isinstance(error, HTTPError):
                    record['http_status'] = error.code
                    retry = error.headers.get('Retry-After')
                    if retry:
                        record['retry_after'] = retry
                        try: next_allowed = time.time()+float(retry)
                        except ValueError: next_allowed = parsedate_to_datetime(retry).timestamp()
                print('FAILED', request['target'], record, flush=True)
            request['attempts'].append(record)
            MANIFEST.write_text(json.dumps(requests, indent=2)+'\n')
            if request.get('downloaded'):
                print('VALIDATED', request['target'], flush=True)
                break
        if not request.get('downloaded'):
            raise SystemExit('DOWNLOAD GATE BLOCKED: '+json.dumps(request))
    print('All eight OASIS reports validated', flush=True)


if __name__ == '__main__':
    main()
