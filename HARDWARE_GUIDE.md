# Hardware Assembly Guide
## Mouse Trap Monitoring System

---

## Bill of Materials (BOM)

### Per Trap Node ($8-12 each)

| Component | Quantity | Price | Source |
|-----------|----------|-------|--------|
| Seeed XIAO ESP32-C3 | 1 | $4-5 | Amazon, Seeed |
| Victor M325 Mouse Trap | 1 | $0.64-1.00 | Amazon, Hardware Store |
| MC-38 Reed Switch | 1 | $0.30-0.50 | Amazon, AliExpress |
| 6mm×3mm Neodymium Magnet | 1 | $0.20 | Amazon, AliExpress |
| LiPo Battery 800-2500mAh | 1 | $4-6 | Amazon |
| 220Ω Resistor (optional LED) | 1 | $0.05 | Amazon |
| 3mm LED (optional) | 1 | $0.10 | Amazon |
| 22AWG Wire | ~12" | $0.20 | Amazon |
| Heat Shrink Tubing | ~6" | $0.10 | Amazon |
| Hot Glue | As needed | - | - |

**Total per node: $8-12**

### Gateway (One-time purchase)

| Component | Quantity | Price |
|-----------|----------|-------|
| ESP32 or ESP32-C3 Dev Board | 1 | $3-5 |
| USB Cable | 1 | $2-3 |
| USB Power Adapter | 1 | $3-5 |

**Total: $8-13**

### Server (One-time purchase)

| Component | Quantity | Price |
|-----------|----------|-------|
| Raspberry Pi (3B+ or newer) | 1 | $15-50 |
| MicroSD Card (8GB+) | 1 | $5-10 |
| Power Supply | 1 | $5-8 |

**Total: $25-68**

---

## Wiring Diagrams

### Trap Node (ESP32-C3) Wiring

```
┌─────────────────────────────────────────┐
│      Seeed XIAO ESP32-C3                │
│                                         │
│  ┌───┐                                  │
│  │USB│                                  │
│  └───┘                                  │
│                                         │
│  [5V] [GND] [3V3] [D0] ... [D9] [D10]  │
│    │    │     │              │          │
└────┼────┼─────┼──────────────┼──────────┘
     │    │     │              │
     │    │     │              └─────┬─── Reed Switch Terminal 1
     │    │     │                    │
     │    │     └──────────────── Optional LED (with 220Ω) ───┐
     │    │                                                    │
     │    └───────────────────── Reed Switch Terminal 2 ──────┤
     │                                  (via GND)             │
     │                                                         │
     └─ LiPo Battery (BAT+ on underside) ────────────────────┘

```

**Pin Connections:**
- **GPIO9 (D9)**: Reed switch terminal 1
- **GND**: Reed switch terminal 2
- **GPIO3 (D3)**: Optional status LED (+ terminal via 220Ω resistor)
- **GND**: LED (- terminal)
- **BAT+/BAT-**: LiPo battery JST connector (on underside of board)

### Reed Switch Installation

```
Side View of Mouse Trap:
                           
    ┌─────────────────┐
    │   Bait Cup      │
    └────────┬────────┘
         ┌───┴───┐         ← Striker Bar (moving part)
         │ ⊗ ⊗ ⊗ │         ← Magnet hot-glued here
         └───────┘
    
    [REED SWITCH]          ← Hot-glued to trap base
         ▼▼▼
    ═══════════════════    ← Trap Base (stationary)
```

**Assembly Steps:**

1. **Position Reed Switch:**
   - Place reed switch flat on trap base
   - Position ~5mm from striker bar rest position
   - Hot glue in place (use generous amount)

2. **Attach Magnet:**
   - Hot glue 6mm×3mm magnet to striker bar
   - Align directly above reed switch
   - Test: When trap snaps, magnet should be ~2-3mm from switch

3. **Wire Connections:**
   - Solder 22AWG wire to reed switch terminals
   - Cover connections with heat shrink tubing
   - Route wires to ESP32-C3 location

4. **Mount ESP32-C3:**
   - Hot glue ESP32-C3 to side of trap base
   - Ensure USB port is accessible for programming
   - Leave battery connector accessible

5. **Connect Battery:**
   - Plug LiPo battery into JST connector
   - Secure battery with hot glue or zip tie
   - Ensure battery won't interfere with trap mechanism

### Testing Reed Switch

Use multimeter in continuity mode:

```
Trap Open (Set):
Reed Switch: OPEN CIRCUIT (∞ Ω)

Trap Closed (Snapped):
Reed Switch: CLOSED CIRCUIT (0 Ω)
```

**Troubleshooting:**
- If switch doesn't close: Magnet too far, move switch closer
- If switch always closed: Magnet too close, reposition
- Optimal gap: 2-5mm when trap is snapped

---

## Gateway Wiring

### ESP32 Gateway (USB Powered)

```
┌─────────────────────────────────┐
│         ESP32 Gateway           │
│                                 │
│  ┌────┐                         │
│  │USB │ ← 5V Power (Always On)  │
│  └────┘                         │
│                                 │
│  Built-in LED on GPIO2          │
│  (No external components)       │
└─────────────────────────────────┘
```

**Gateway Setup:**
- Connect via USB to power adapter
- No external components needed
- Built-in LED indicates status
- Must stay powered 24/7

---

## Power Consumption & Battery Life

### Trap Node Power Profile

```
Operating Mode        Current    Duration      Energy
──────────────────────────────────────────────────────
Deep Sleep           44 µA      ~99.9% time   0.044 mA
Wake + RF TX         140 mA     50 ms         0.007 mAh
Wake (no trigger)    25 mA      200 ms        0.005 mAh
──────────────────────────────────────────────────────
Average per day                               ~0.15 mAh
```

### Expected Battery Life

| Battery Capacity | Expected Life |
|------------------|---------------|
| 800 mAh | 6 months |
| 1500 mAh | 12 months |
| 2500 mAh | 18+ months |

**Factors affecting battery life:**
- Trap trigger frequency
- Environmental temperature
- RF signal strength
- Number of mesh hops

---

## Physical Assembly Tips

### Weatherproofing (Optional)

For outdoor or damp locations:

1. **Conformal Coating:**
   - Spray PCB with conformal coating
   - Avoid coating connectors and switches
   - Let dry 24 hours

2. **Enclosure:**
   - Small plastic project box
   - Cut opening for trap mechanism
   - Seal with silicone caulk

3. **Wire Protection:**
   - Use outdoor-rated wire
   - Apply heat shrink to all connections
   - Seal entry points with hot glue

### Cable Management

```
        ESP32-C3
           │
           │ ← Keep wires short
           │    (<6 inches)
           │
      Reed Switch
```

**Best Practices:**
- Use different colored wires (red/black)
- Label each node with marker
- Keep wire routing neat
- Avoid sharp bends that could break

---

## Safety & Handling

### Battery Safety

⚠️ **IMPORTANT:**
- Use LiPo batteries with protection circuit
- Never puncture or short circuit
- Charge in fire-safe area
- Dispose properly when damaged

### Trap Safety

⚠️ **CAUTION:**
- Mouse traps can cause injury
- Keep away from children and pets
- Test mechanism carefully
- Use proper bait handling

---

## Testing Procedure

### 1. Initial Power-On Test

1. Connect battery to ESP32-C3
2. LED should blink twice (startup)
3. Connect to Serial Monitor (115200 baud)
4. Verify MAC address is displayed
5. Check battery voltage reading

### 2. Reed Switch Test

1. With serial monitor open
2. Manually trigger reed switch with magnet
3. Should see "TRAP TRIGGERED" message
4. LED should blink 5 times
5. Device should transmit, then sleep

### 3. Range Test

1. Place node near gateway
2. Trigger trap
3. Verify MQTT message received
4. Move node progressively farther
5. Document maximum range

### 4. Battery Life Test

1. Note starting battery voltage
2. Let node operate normally
3. Check voltage after 24 hours
4. Calculate daily drain
5. Estimate total battery life

---

## Recommended Node Placement

### Optimal Locations

```
Floor Plan Example:

Kitchen     Garage      Basement
  [T1]       [T2]         [T3]
   │          │            │
   │          │            │
   └────[Gateway]──────────┘
            │
        (to Pi via WiFi)
```

**Guidelines:**
- Max 30-50m between nodes
- Nodes can relay for extended range
- Gateway needs strong WiFi signal
- Avoid metal barriers
- Higher placement = better RF

---

## Troubleshooting Guide

### Node Won't Power On
- Check battery voltage (should be >3.3V)
- Verify JST connector orientation
- Try different battery
- Check for shorts in wiring

### Reed Switch Not Triggering
- Test with multimeter
- Check magnet polarity (any side works)
- Verify wiring connections
- Reduce gap between switch and magnet

### No MQTT Messages
- Verify gateway is online
- Check node MAC address in firmware
- Test MQTT broker: `mosquitto_sub -t "trap/#"`
- Check WiFi signal strength

### Poor Battery Life
- Verify deep sleep is working
- Check for code errors keeping device awake
- Reduce status update frequency
- Use larger battery

---

## Maintenance Schedule

### Weekly
- Check MQTT message log
- Verify all nodes reporting
- Test Telegram notifications

### Monthly
- Check battery voltages
- Clean reed switches
- Verify trap mechanisms
- Review catch statistics

### Quarterly
- Replace batteries as needed
- Update firmware if available
- Backup database
- Review system performance

---

## Scaling the System

### Adding More Nodes

1. Flash firmware with unique NODE_ID
2. Update config.yaml with location
3. Power on and verify connection
4. Monitor MQTT for first message
5. Update dashboard

### Mesh Network Expansion

```
Building Layout:

House           Garage          Shed
[T1][T2]    →   [T3]        →  [T4]
    │               │              │
    └───[Gateway]───┘              │
           │                       │
       (WiFi Range)        (Mesh Extended)
```

Nodes automatically relay messages to extend range beyond WiFi coverage.

---

## Next Steps

After hardware assembly:

1. ✅ Flash firmware to nodes
2. ✅ Configure gateway
3. ✅ Setup Raspberry Pi
4. ✅ Test MQTT communication
5. ✅ Configure Telegram
6. ✅ Access web dashboard
7. ✅ Deploy traps
8. ✅ Monitor and optimize

---

**Questions or issues? Check the GitHub repository for updates and community support!**
