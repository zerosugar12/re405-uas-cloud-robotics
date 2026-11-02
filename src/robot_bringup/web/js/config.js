const host = window.location.hostname;
const isLocal = host === 'localhost' || host === '127.0.0.1';

export const config = {
  isLocal,
  WS_BASE: isLocal ? 'http://localhost:8080' : 'http://xxx.xxx.xxx.xxx/camera',
  ROSBRIDGE_URL: window.ROSBRIDGE_URL || (isLocal ? 'ws://localhost:9090' : 'ws://xxx.xxx.xxx.xxx/rosbridge'),
  CAMERA_TOPIC: '/annotated_image',
  ODOM_TOPIC: '/odom',
  BALL_DISTANCE_TOPIC: '/ball_distance',
  BALL_WORLD_TOPIC: '/ball_world',
  LATENCY_PING_TOPIC: '/latency_ping',
  LATENCY_PONG_TOPIC: '/latency_pong',
  CMD_VEL_TOPIC: '/cmd_vel',
};