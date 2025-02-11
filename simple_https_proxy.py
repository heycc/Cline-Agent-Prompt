from flask import Flask, request, Response, stream_with_context
import requests


app = Flask(__name__)
target_base = 'https://example.com'  # 默认目标地址


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    body = request.get_data()
    print(f"\nRequest Body:\n{body.decode('utf-8')}\n")

    # 构造目标 URL
    target_url = f"{target_base.rstrip('/')}/{path}"
    
    # 转发请求（跳过 Host 头）
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    
    # 发送请求到目标服务器
    resp = requests.request(
        method=request.method,
        url=target_url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        stream=True,  # 启用流式请求
        verify=False  # 跳过 SSL 验证（生产环境不推荐）
    )
    
    # 构造返回响应（排除敏感头信息）
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [
        (k, v) for k, v in resp.raw.headers.items()
        if k.lower() not in excluded_headers
    ]
    
    # 根据远程服务的响应类型决定是否以流式方式返回
    if 'transfer-encoding' in resp.headers and resp.headers['transfer-encoding'].lower() == 'chunked':
        # 流式响应
        return Response(stream_with_context(resp.iter_content(chunk_size=8192)), resp.status_code, headers)
    else:
        # 非流式响应
        return Response(resp.content, resp.status_code, headers)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Simple HTTP Proxy')
    parser.add_argument('--target', required=True, help='Target URL (e.g. https://example.com)')
    parser.add_argument('--port', type=int, default=8080, help='Proxy port')
    args = parser.parse_args()
    
    target_base = args.target
    app.run(host='0.0.0.0', port=args.port)
