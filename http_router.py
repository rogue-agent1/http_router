#!/usr/bin/env python3
"""HTTP Router — trie-based URL routing with path params and middleware."""
import re

class RouteNode:
    def __init__(self):
        self.children = {}; self.handler = None; self.param_name = None; self.middleware = []

class Router:
    def __init__(self): self.root = RouteNode(); self.global_middleware = []
    def use(self, mw): self.global_middleware.append(mw)
    def add(self, method, path, handler, middleware=None):
        key = f"{method.upper()}:"
        parts = path.strip('/').split('/')
        node = self.root
        for part in [key] + parts:
            if part.startswith(':'):
                if '*' not in node.children: node.children['*'] = RouteNode()
                node = node.children['*']; node.param_name = part[1:]
            else:
                if part not in node.children: node.children[part] = RouteNode()
                node = node.children[part]
        node.handler = handler; node.middleware = middleware or []
    def get(self, path, handler, **kw): self.add('GET', path, handler, **kw)
    def post(self, path, handler, **kw): self.add('POST', path, handler, **kw)
    def match(self, method, path):
        parts = path.strip('/').split('/'); params = {}
        node = self.root; key = f"{method.upper()}:"
        if key not in node.children: return None, {}
        node = node.children[key]
        for part in parts:
            if part in node.children: node = node.children[part]
            elif '*' in node.children:
                node = node.children['*']; params[node.param_name] = part
            else: return None, {}
        if node.handler:
            chain = self.global_middleware + node.middleware + [node.handler]
            return chain, params
        return None, {}
    def dispatch(self, method, path):
        chain, params = self.match(method, path)
        if not chain: return {"status": 404, "body": "Not Found"}
        ctx = {"method": method, "path": path, "params": params}
        for fn in chain:
            result = fn(ctx)
            if result: return result
        return {"status": 200}

if __name__ == "__main__":
    r = Router()
    r.use(lambda ctx: None)  # logging middleware
    r.get("/users", lambda ctx: {"status": 200, "body": "user list"})
    r.get("/users/:id", lambda ctx: {"status": 200, "body": f"user {ctx['params']['id']}"})
    r.post("/users", lambda ctx: {"status": 201, "body": "created"})
    r.get("/users/:id/posts/:post_id", lambda ctx: {"status": 200, "body": f"post {ctx['params']}"})
    for m, p in [("GET","/users"), ("GET","/users/42"), ("POST","/users"), ("GET","/users/1/posts/99"), ("GET","/missing")]:
        print(f"  {m} {p} → {r.dispatch(m, p)}")
