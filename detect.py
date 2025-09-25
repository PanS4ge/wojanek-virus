import subprocess, json, re, sys

VM_KEYWORDS = {
    "manufacturer": [
        "microsoft corporation",  # Hyper-V
        "vmware, inc.", "vmware",
        "innotek gmbh", "oracle corporation", "virtualbox",
        "xen", "xenserver", "citrix",
        "qemu", "kvm",
        "parallels", "bochs"
    ],
    "model": [
        "virtual machine", "vmware virtual platform",
        "virtualbox", "kvm", "qemu", "hyper-v"
    ],
    "bios": [
        "vmware", "virtualbox", "hyper-v", "xen", "qemu", "sea bios", "seabios"
    ],
    "board": [
        "vmware", "virtualbox", "qemu", "xen", "hyper-v"
    ],
}

# Prefiksy MAC popularnych hypervisorów (nie wyczerpujące, ale praktyczne)
VM_MAC_PREFIXES = {
    "VMware": {"00:05:69", "00:0C:29", "00:1C:14", "00:50:56"},
    "VirtualBox": {"08:00:27"},
    "Hyper-V": {"00:15:5D"},
    "Parallels": {"00:1C:42"},
    "QEMU/KVM": {"52:54:00"},
}

VM_SERVICE_NAMES = [
    "vmtools", "vmtoolsd", "vgauthservice",     # VMware Tools
    "vboxservice", "vboxtray",                  # VirtualBox Guest Additions
    "qemu-ga",                                  # QEMU guest agent
    "hypervguest", "vmicheartbeat", "vmicrdv", "vmicvss", "vmicshutdown", "vmickvpexchange"  # Hyper-V integ.
]

def _ps(cmd):
    """Run a PowerShell command and return stdout text (or '')"""
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True, text=True, timeout=10
        )
        return completed.stdout.strip()
    except Exception:
        return ""

def _any_contains(text, keywords):
    t = (text or "").lower()
    return any(k in t for k in keywords)

def evidence_wmi():
    # Zbieramy podstawowe identyfikatory sprzętu
    cmd = r"""
    $o = [ordered]@{}
    $cs = Get-CimInstance Win32_ComputerSystem
    $bios = Get-CimInstance Win32_BIOS
    $bb = Get-CimInstance Win32_BaseBoard
    $csp = Get-CimInstance Win32_ComputerSystemProduct
    $o.manufacturer = $cs.Manufacturer
    $o.model = $cs.Model
    $o.bios_vendor = $bios.Manufacturer
    $o.bios_version = ($bios.SMBIOSBIOSVersion -join ' ')
    $o.baseboard = "$($bb.Manufacturer) $($bb.Product)"
    $o.uuid = $csp.UUID
    $o | ConvertTo-Json -Compress
    """
    raw = _ps(cmd)
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {}
    ev = []
    score = 0

    manu = data.get("manufacturer","")
    model = data.get("model","")
    bios_vendor = data.get("bios_vendor","")
    bios_version = data.get("bios_version","")
    baseboard = data.get("baseboard","")
    uuid = data.get("uuid","")

    if _any_contains(manu, VM_KEYWORDS["manufacturer"]):
        ev.append(f"Manufacturer: {manu}")
        score += 2
    if _any_contains(model, VM_KEYWORDS["model"]):
        ev.append(f"Model: {model}")
        score += 2
    if _any_contains(bios_vendor + " " + bios_version, VM_KEYWORDS["bios"]):
        ev.append(f"BIOS: {bios_vendor} {bios_version}".strip())
        score += 1
    if _any_contains(baseboard, VM_KEYWORDS["board"]):
        ev.append(f"Baseboard: {baseboard}")
        score += 1

    # Niektóre hypervisory używają "specjalnych" UUID (np. wiele zer)
    if uuid and re.match(r"^0{8}-0{4}-0{4}-0{4}-0{12}$", uuid):
        ev.append(f"Podejrzany UUID: {uuid}")
        score += 1

    return score, ev

def evidence_registry_hyperv():
    # Klucz obecny w gościu Hyper-V
    cmd = r"Test-Path 'HKLM:\SOFTWARE\Microsoft\Virtual Machine\Guest\Parameters'"
    out = _ps(cmd)
    if out.strip().lower() == "true":
        return 2, ["HKLM:\\SOFTWARE\\Microsoft\\Virtual Machine\\Guest\\Parameters istnieje (Hyper-V)"]
    return 0, []

def evidence_services_processes():
    # Szukamy charakterystycznych usług/procesów
    cmd = r"Get-Process | Select-Object -ExpandProperty Name"
    procs = set(n.lower() for n in _ps(cmd).splitlines())
    hits = []
    score = 0
    for name in VM_SERVICE_NAMES:
        if any(p.startswith(name) for p in procs):
            hits.append(f"Proces/usługa: {name}")
            score += 1
    return score, hits

def evidence_mac_oui():
    # Pobieramy adresy MAC przez PowerShell (bez psutil)
    cmd = r"Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -Expand MacAddress"
    macs = [m.strip().upper() for m in _ps(cmd).splitlines() if m.strip()]
    found = []
    score = 0
    for mac in macs:
        pref = mac[:8]  # format 'AA:BB:CC'
        for vendor, prefixes in VM_MAC_PREFIXES.items():
            if pref in prefixes:
                found.append(f"MAC {mac} ⇒ {vendor}")
                score += 1
    return score, found

def is_virtual_machine_windows():
    total_score = 0
    all_ev = []

    for fn in (evidence_wmi, evidence_registry_hyperv, evidence_services_processes, evidence_mac_oui):
        s, ev = fn()
        total_score += s
        all_ev.extend(ev)

    # prosty próg; 2–3 = prawdopodobne, 4+ = bardzo prawdopodobne
    verdict = "bare-metal"
    if total_score >= 4:
        verdict = "vm (high confidence)"
    elif total_score >= 2:
        verdict = "vm (likely)"

    return verdict, total_score, all_ev