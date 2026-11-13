from session_cache import SessionCacheManager

def create_app():
    return SessionCacheManager()

if __name__ == "__main__":
    mgr = create_app()
    token = mgr.save_session("user1", {"username": "alice", "role": "admin"})
    print("Session saved:", mgr.get_session("user1"))
