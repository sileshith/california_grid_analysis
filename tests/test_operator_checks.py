import io
import zipfile
import pytest
from src.acquire_operator_checks import validate
from src.audit_replay import compare,differences


def test_error_document_is_not_report():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:z.writestr('error.xml','<error>rate limit</error>')
    with pytest.raises(ValueError,match='Expected one CSV'):
        validate(stream.getvalue(),dict(startdatetime='20250407T07:00-0000',enddatetime='20250414T07:00-0000',market_run_id='DAM'))


def test_relative_difference_uses_absolute_denominator_and_zero_is_undefined():
    a={'authority_metrics':[dict(method='prophet',balancing_authority='CISO',bias_mw=-2.,mae_mw=0.)]}
    b={'authority_metrics':[dict(method='prophet',balancing_authority='CISO',bias_mw=-3.,mae_mw=1.)]}
    result=compare(a,b)
    assert result['bias_mw']['max_relative']['relative']==.5
    assert result['mae_mw']['max_relative'] is None
    assert result['mae_mw']['undefined_relative_authorities']==['CISO']
    assert len(differences(a,b))==2
