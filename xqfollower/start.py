from xq_follower import XueQiuFollower
from xq_ws_mgr import XueQiuWebsocketManager
from xq_track_mgr import XueQiuTrackManager

def main():
    xq = XueQiuFollower()
    ws = XueQiuWebsocketManager(xq, "do_socket_trade")
    track = XueQiuTrackManager(xq, "consume_offline_msg")
    
if __name__ == "__main__":
    main()
