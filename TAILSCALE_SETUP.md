# Tailscale VPS Setup

Guide for installing and configuring **Tailscale** on the VPS to connect the VPS and the PC Robot over a private mesh network (Tailnet). This tunnel lets the VPS (nginx) forward dashboard traffic to the PC Robot without opening public ports on the PC.

> IPs used in this project (example/dummy values):
> - VPS public IP: `xxx.xxx.xxx.xxx`
> - VPS Tailscale IP: `xxx.xxx.xxx.xxx`
> - PC Robot Tailscale IP: `xxx.xxx.xxx.xxx`

## 1. Install Tailscale on the VPS

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

Once installed, log in and register the VPS to your Tailscale account:

```bash
tailscale up
```

The command above will print a URL for authentication. Open it in your browser and sign in with your Tailscale account. After it succeeds, the VPS is added to your Tailnet.

Verify the status:

```bash
tailscale status
tailscale ip -4
```

## 2. Install Tailscale on the PC Robot

Do the same on the PC Robot (the machine running ROS 2 / the simulation):

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

Make sure **both devices are on the same Tailscale account**, then check the connection between them:

```bash
# from the PC Robot, ping the VPS via its Tailscale IP
ping xxx.xxx.xxx.xxx

# from the VPS, ping the PC Robot via its Tailscale IP
ping xxx.xxx.xxx.xxx
```

## 3. Start Tailscale automatically on boot

To keep Tailscale running after the VPS restarts:

```bash
sudo systemctl enable tailscaled
sudo systemctl start tailscaled
```

Check the service status:

```bash
sudo systemctl status tailscaled
```

## 4. Sync the IPs in the scripts

Make sure the Tailscale IPs in the script match the output of `tailscale ip -4` on each device:

- `scripts/deploy_vps.sh`:
  - `VPS_TAILSCALE_IP` = the VPS Tailscale IP
  - `PC_TAILSCALE_IP` = the PC Robot Tailscale IP (used for the nginx `proxy_pass`)

Example:

```bash
VPS_TAILSCALE_IP="xxx.xxx.xxx.xxx"
PC_TAILSCALE_IP="xxx.xxx.xxx.xxx"
```

## 5. Verify the tunnel path nginx → Tailscale → PC Robot

Once everything is connected and nginx is deployed:

```bash
# from the VPS, check the rosbridge port on the PC Robot over Tailscale
curl -s http://xxx.xxx.xxx.xxx:9090

# from the VPS, check the nginx proxy
curl -s http://localhost/rosbridge
```

If both respond, the dashboard is publicly reachable at `http://xxx.xxx.xxx.xxx`.

## Troubleshooting

- **`tailscale up` fails / no URL shown**: make sure `curl` and `systemctl` are available, then re-run `curl -fsSL https://tailscale.com/install.sh | sh`.
- **Ping between devices fails**: make sure both devices are signed in to the same Tailscale account, and that the ACLs in the Tailscale admin console allow traffic between devices.
- **Port 9090/8080 unreachable over Tailscale**: make sure rosbridge / web-video-server on the PC Robot binds to `0.0.0.0`, not just `localhost`.
- **To disable temporarily**: run `sudo tailscale down` on the VPS.