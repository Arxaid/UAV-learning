# This file is part of UAV-learning repo.
#
# Feel free to use, copy, modify, merge and publish this software.

import rospy
from geometry_msgs.msg import PoseStamped
from mavros_msgs.msg import State

import src.controlFunctions as control

rospy.init_node('UAV-learning')

if __name__ == '__main__':

    app = control.ControlFunctions(takeoffHeight=2)
    stateSubscriber = rospy.Subscriber('mavros/state', data_class=State, callback=app.state_callback)
    poseSubscriber = rospy.Subscriber('mavros/local_position/pose', data_class=PoseStamped, callback=app.pose_callback)

    while not rospy.is_shutdown():
        app.takeoff()
        app.landing()
        app.lastRequest = rospy.Time.now()
        app.rate.sleep()