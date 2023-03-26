# This file is part of UAV-learning repo.
#
# Feel free to use, copy, modify, merge and publish this software.

import rospy
from geometry_msgs.msg import PoseStamped
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, CommandBoolRequest, CommandTOL
from mavros_msgs.srv import SetMode, SetModeRequest

class ControlFunctions():
    def __init__(self, takeoffHeight):
        self.currentState = State()
        self.currentPose = PoseStamped()
        self.lastRequest = rospy.Time.now()
        self.lastArmingRequest = rospy.Time.now()
        self.lastSetModeRequest = rospy.Time.now()
        self.rate = rospy.Rate(20)
        self.takeoffHeight = takeoffHeight
        self.onLand = True
        self.isLanding = False

        rospy.wait_for_service('/mavros/cmd/arming')
        self.armingClient = rospy.ServiceProxy('/mavros/cmd/arming', CommandBool)
        rospy.wait_for_service('/mavros/set_mode')
        self.setModeClient = rospy.ServiceProxy('/mavros/set_mode', SetMode)

        rospy.wait_for_service('mavros/cmd/takeoff')
        self.takeoffService = rospy.ServiceProxy('mavros/cmd/takeoff', CommandTOL)
        rospy.wait_for_service('mavros/cmd/land')
        self.landService = rospy.ServiceProxy('mavros/cmd/land', CommandTOL)
    
    def state_callback(self, msg):
        self.currentState = msg

    def pose_callback(self, msg):
        self.currentPose = msg

    def arming_callback(self, cmd):
        _response = False
        armingCommand = CommandBoolRequest()
        armingCommand.value = cmd
        if self.currentState.armed != cmd:
            if (rospy.Time.now() - self.lastArmingRequest) > rospy.Duration(5.0):
                self.lastArmingRequest = rospy.Time.now()
                if self.armingClient.call(armingCommand).success == True:
                    rospy.loginfo('UAV armed')
                    _response= True
        else:
            _response = True
        return _response
    
    def mode_callback(self, mode):
        _response = False
        setMode = SetModeRequest()
        setMode.custom_mode = mode
        if self.currentState.mode != mode:
            if (rospy.Time.now() - self.lastSetModeRequest) > rospy.Duration(5.0):
                self.lastSetModeRequest = rospy.Time.now()
                if self.setModeClient.call(setMode).mode_sent == True:
                    rospy.loginfo('%s enabled', mode)
                    _response = True
        else:
            _response = True
        return _response
    
    def wait_for_connection(self):
        while not rospy.is_shutdown() and not self.currentState.connected():
            self.rate.sleep()

    def takeoff(self):
        if self.onLand:
            self.arming_callback(True)
            self.onLand = False

        if self.currentPose.pose.position.z < self.takeoffHeight and not self.isLanding:
            if self.mode_callback('AUTO.TAKEOFF'):
                self.arming_callback(True)

        if self.currentPose.pose.position.z >= self.takeoffHeight and not self.isLanding:
            rospy.loginfo('Takeoff height achieved')
            self.isLanding = True
            return
    
    def landing(self):
        if self.isLanding:
            if self.mode_callback('AUTO.LAND'):
                self.arming_callback(True)
        
        if self.currentPose.pose.position.z < 0.1 and self.isLanding:
            rospy.loginfo('UAV landed successfully')
            self.arming_callback(False)
            self.isLanding = False
            self.onLand = True
            return