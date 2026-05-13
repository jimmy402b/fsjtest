"""Vive Tracker pose reader — libsurvive Python bindings wrapper."""


class Tracker:
    def __init__(self):
        import libsurvive
        self._ctx = libsurvive.init()
        self._ctx.start()

    def get_pose(self):
        self._ctx.poll()
        pose = self._ctx.lighthouse_pose()
        if pose is None:
            return None
        return {
            'x': pose.Pos[0],
            'y': pose.Pos[1],
            'z': pose.Pos[2],
            'qw': pose.Rot[0],
            'qx': pose.Rot[1],
            'qy': pose.Rot[2],
            'qz': pose.Rot[3],
        }

    def close(self):
        self._ctx.close()
