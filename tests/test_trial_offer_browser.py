"""TRR-01/02/03/04/10/11: exercise shipped dialogs in an isolated browser.

No account or agent data is seeded. Only the billing/status API is stubbed;
HTML/CSS/JS are the actual no-build assets that ship in the wheel.

AC-GUX-TRR-001.1
AC-GUX-TRR-001.2
AC-GUX-TRR-001.4
AC-GUX-TRR-001.5
AC-GUX-TRR-001.6
"""
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'clawmetry/static'
APP = (STATIC / 'js/app.js').read_text()
START = APP.index('(function initClawMetryHardBlockOverlay()')
END = APP.index('\n})();', START) + len('\n})();')


@pytest.fixture
def offer(_shared_chromium, tmp_path):
    context = _shared_chromium.new_context(viewport={'width':1280,'height':720})
    page = context.new_page()
    calls, errors = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    state = {'hard_blocked':True,'expired':True,'tier':'trial','reason':'Your ClawMetry trial has ended.',
             'free_runtimes':['openclaw','nemoclaw','goose','qwen_code']}
    def respond(route):
        request = route.request
        path = request.url.split('trial.test',1)[1]
        calls.append((path, request.method, request.post_data))
        if path == '/':
            route.fulfill(content_type='text/html', body='''<!doctype html><html data-theme="dark"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/static/css/dashboard.css"></head><body><button id="behind">Dashboard</button><div id="cm-trial-pill-slot"></div>
<script src="/static/js/trial-offer.js"></script><script src="/component.js"></script>
<script src="/static/js/trial-pill.js"></script></body></html>''')
        elif path == '/component.js':
            route.fulfill(content_type='text/javascript', body=APP[START:END])
        elif path.startswith('/static/'):
            asset=STATIC / path.removeprefix('/static/')
            if asset.is_file():
                route.fulfill(path=str(asset))
            else:
                route.fulfill(status=404,body='Asset unavailable')
        elif path in ('/api/trial/status','/api/trial/refresh-license'):
            route.fulfill(json=state)
        elif path == '/api/trial/extension':
            route.fulfill(json={'eligible':True,'free_days':60} if request.method == 'GET' else
                          {'ok':True,'grant_state':'applied','trial_end':'2027-01-05T08:00:00Z'})
        else:
            route.fulfill(json={})
    page.route('http://trial.test/**', respond)
    yield page, calls, errors, state, tmp_path
    context.close()


def screenshot(page, name, tmp_path):
    directory = Path(os.environ.get('CLAWMETRY_TRIAL_SCREENSHOT_DIR', str(tmp_path)))
    directory.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(directory / (name + '.png')), full_page=True)


@pytest.mark.parametrize('width,height', [(1280,720),(375,812),(320,568),(640,360)])
def test_expired_offer_fits_and_actions_remain_reachable(offer,width,height):
    page,calls,errors,_,tmp_path=offer
    page.set_viewport_size({'width':width,'height':height})
    page.goto('http://trial.test/')
    dialog=page.get_by_role('dialog')
    dialog.wait_for()
    box=dialog.locator('.cm-offer-card, .cm-hbo-card').bounding_box()
    directory = Path(os.environ.get('CLAWMETRY_TRIAL_SCREENSHOT_DIR', str(tmp_path)))
    directory.mkdir(parents=True,exist_ok=True)
    (directory / f'layout-{width}x{height}.json').write_text(json.dumps(box))
    screenshot(page,f'trial-monthly-{width}x{height}',tmp_path)
    assert box['width'] <= min(440,width-32), box
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    if height>=720:
        assert box['y']>=0 and box['y']+box['height'] <= height
    assert not page.get_by_label('License key',exact=True).is_visible()
    assert 'Waiting for payment' not in dialog.inner_text()
    assert not any(path=='/api/trial/extension' for path,_,_ in calls)
    page.get_by_role('button',name='Use a license key',exact=True).scroll_into_view_if_needed()
    assert page.get_by_role('button',name='Continue free',exact=True).is_visible()
    assert 'Other runtimes need a subscription' in dialog.inner_text()
    screenshot(page,f'trial-monthly-{width}x{height}',tmp_path)
    if width==1280:
        page.get_by_role('button',name='Annual',exact=False).click()
        box=dialog.locator('.cm-offer-card, .cm-hbo-card').bounding_box()
        assert box['y']+box['height']<=height
        assert '$90' in dialog.inner_text() and '$190' in dialog.inner_text()
        screenshot(page,'trial-annual-1280x720',tmp_path)
    assert not errors


def test_decline_feedback_confirm_date_and_no_background_request(offer):
    page,calls,errors,_,tmp_path=offer
    page.goto('http://trial.test/')
    page.get_by_role('button',name='Not ready to subscribe?').click()
    page.get_by_role('button',name='Extend my trial',exact=True).wait_for()
    assert sum(path=='/api/trial/extension' for path,_,_ in calls)==1
    assert not any(path=='/api/trial/extension' and method=='POST' for path,method,_ in calls)
    assert 'No card required. No automatic charge.' in page.get_by_role('dialog').inner_text()
    screenshot(page,'trial-feedback-1280x720',tmp_path)
    page.get_by_label('What stopped you upgrading?').select_option('price')
    page.get_by_label('What would make it worth subscribing?').fill('More useful insights')
    page.get_by_role('button',name='Extend my trial',exact=True).click()
    page.get_by_role('button',name='Continue to dashboard',exact=True).wait_for()
    assert 'January 5, 2027' in page.get_by_role('dialog').inner_text()
    posted=[json.loads(body) for path,method,body in calls if path=='/api/trial/extension' and method=='POST']
    assert posted==[{'reason':'price','feedback':'More useful insights'}]
    screenshot(page,'trial-confirmed-1280x720',tmp_path)
    assert not errors


def test_focus_and_optional_modal_share_the_compact_component(offer):
    page,_,errors,state,tmp_path=offer
    state.update(hard_blocked=False,expired=False,days_until_expiry=2)
    page.goto('http://trial.test/')
    page.get_by_role('button',name='Upgrade',exact=True).click()
    dialog=page.get_by_role('dialog')
    dialog.wait_for()
    assert page.locator(':focus').evaluate('(node)=>node.tagName')=='H2'
    page.keyboard.press('Shift+Tab')
    assert page.locator(':focus').evaluate('(node)=>!!node.closest(".cm-offer-card")')
    page.keyboard.press('Tab')
    assert page.locator(':focus').evaluate('(node)=>!!node.closest(".cm-offer-card")')
    assert not page.get_by_role('button',name='Not ready to subscribe?').count()
    screenshot(page,'trial-pre-expiry-1280x720',tmp_path)
    page.keyboard.press('Escape')
    assert not dialog.count()
    assert not errors
