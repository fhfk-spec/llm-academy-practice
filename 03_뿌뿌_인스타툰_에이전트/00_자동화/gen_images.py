"""
뿌뿌 인스타툰 - 이미지 자동 생성기 (OpenAI 이미지 API)

사용법:  python gen_images.py <콘티 프롬프트 json> <출력 폴더>
- API 키: 같은 폴더(또는 상위 '인스타툰' 폴더)의 openai_key.txt 한 줄
- 레퍼런스: refs/ 폴더의 이미지들(시안 기본포즈, 표정 등)을 매 컷에 함께 첨부
"""
import base64, json, os, sys, time, pathlib, urllib.request, urllib.error, mimetypes, uuid

HERE = pathlib.Path(__file__).resolve().parent
MODEL = os.environ.get('PPUPPU_MODEL', 'gpt-image-2.5-flare')
SIZE = os.environ.get('PPUPPU_SIZE', '1088x1360')        # 4:5, 16의 배수
QUALITY = os.environ.get('PPUPPU_QUALITY', 'medium')
API = 'https://api.openai.com/v1/images/edits'


def find_key():
    for p in [HERE / 'openai_key.txt', HERE.parent / 'openai_key.txt']:
        if p.exists():
            k = p.read_text(encoding='utf-8').strip()
            if k:
                return k
    k = os.environ.get('OPENAI_API_KEY')
    if k:
        return k
    sys.exit('openai_key.txt 를 찾을 수 없어요.')


def data_url(path):
    mime = mimetypes.guess_type(str(path))[0] or 'image/png'
    return f'data:{mime};base64,' + base64.b64encode(pathlib.Path(path).read_bytes()).decode()


def post_json(key, body):
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method='POST',
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def post_multipart(key, fields, files):
    b = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, p in files:
        mime = mimetypes.guess_type(str(p))[0] or 'image/png'
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{pathlib.Path(p).name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()
                     + pathlib.Path(p).read_bytes() + b'\r\n')
    parts.append(f'--{b}--\r\n'.encode())
    req = urllib.request.Request(API, data=b''.join(parts), method='POST',
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': f'multipart/form-data; boundary={b}'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def generate(key, prompt, refs):
    body = {'model': MODEL, 'prompt': prompt, 'size': SIZE, 'quality': QUALITY, 'n': 1,
            'images': [{'image_url': data_url(p)} for p in refs]}
    try:
        return post_json(key, body)
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors='replace')
        if e.code in (400, 415) and 'image' in msg.lower():   # 예전 방식(multipart)으로 재시도
            fields = {'model': MODEL, 'prompt': prompt, 'size': SIZE, 'quality': QUALITY, 'n': '1'}
            return post_multipart(key, fields, [('image[]', p) for p in refs])
        raise RuntimeError(f'HTTP {e.code}: {msg[:600]}')


def main():
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
    out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    key = find_key()
    common = spec['common']
    base_refs = [HERE / 'refs' / r for r in spec.get('refs', [])]
    log = []
    for cut in spec['cuts']:
        target = out / f"{cut['id']}.png"
        if target.exists() and not cut.get('force'):
            print('skip', target.name); continue
        refs = base_refs + [HERE / 'refs' / r for r in cut.get('refs', [])]
        prompt = common + '\n\n' + cut['scene']
        for attempt in range(3):
            try:
                t = time.time()
                res = generate(key, prompt, refs)
                img = res['data'][0]
                raw = base64.b64decode(img['b64_json']) if 'b64_json' in img else urllib.request.urlopen(img['url']).read()
                target.write_bytes(raw)
                usage = res.get('usage', {})
                log.append({'id': cut['id'], 'sec': round(time.time() - t, 1), 'usage': usage})
                print('ok', target.name, usage)
                break
            except Exception as e:
                print('retry', cut['id'], e)
                time.sleep(5 * (attempt + 1))
        else:
            print('FAIL', cut['id'])
    (out / 'generation_log.json').write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
