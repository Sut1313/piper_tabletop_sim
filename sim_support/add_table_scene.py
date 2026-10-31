import rclpy
from rclpy.node import Node
from moveit_msgs.srv import ApplyPlanningScene
from moveit_msgs.msg import PlanningScene, CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose

rclpy.init(); node=Node('add_table_scene')
cli=node.create_client(ApplyPlanningScene, '/apply_planning_scene')
if not cli.wait_for_service(timeout_sec=10):
    print('no service'); raise SystemExit(1)
obj=CollisionObject(); obj.id='table'; obj.header.frame_id='base_link'; obj.operation=CollisionObject.ADD
box=SolidPrimitive(); box.type=SolidPrimitive.BOX; box.dimensions=[0.82,0.68,0.05]
pose=Pose(); pose.position.x=0.381; pose.position.y=0.0; pose.position.z=-0.025; pose.orientation.w=1.0
obj.primitives=[box]; obj.primitive_poses=[pose]
scene=PlanningScene(); scene.is_diff=True; scene.world.collision_objects=[obj]
req=ApplyPlanningScene.Request(); req.scene=scene
fut=cli.call_async(req); rclpy.spin_until_future_complete(node,fut,timeout_sec=10)
print('response', None if not fut.done() else fut.result())
