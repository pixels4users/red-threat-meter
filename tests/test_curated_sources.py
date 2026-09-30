import pytest
from osint_dashboard.curated_sources import parse_document, collect_documents
from osint_dashboard.common import load_config

TEXT='SYNTHETIC TEST. An official statement with historical dates and a correction. '*4

@pytest.mark.parametrize('parser',['lv_mod','lv_vdd'])
def test_primary_body_date_and_surrounding_links(parser):
    if parser=='lv_mod':
        html=f'<h1>TEST SYNTHETYCZNY</h1><div class="l-content-main"><div class="field--name-body">{TEXT}<script>SECRET</script></div><div class="field--name-field-publishing-date-time">20.08.2026</div></div>'
    else:
        html=f'<article class="article-block"><h1>TEST SYNTHETYCZNY</h1><time datetime="2026-08-20"></time><div class="article-content">{TEXT}<script>SECRET</script></div></article>'
    item=parse_document((html+'<aside>Unrelated news</aside>').encode(),parser)
    assert item['source_record']=={'published_on':'2026-08-20','publication_date_precision':'day'}
    assert item['published_at'] is None
    assert 'SECRET' not in item['text'] and 'Unrelated' not in item['text']
    with pytest.raises(ValueError):parse_document(b'<h1>Empty</h1>',parser)


def test_selected_documents_never_certify_feed_completeness():
    s=next(s for s in load_config()['sources'] if s['id']=='lv_mod')
    class Fetcher:
        raw_refs=[]
        def get(self,url):raise TimeoutError('Synthetic test')
    result=collect_documents(s,Fetcher())
    assert result['status']=='error' and not result['window_complete']
