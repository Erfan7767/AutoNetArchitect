"""Minimal Windows desktop shell for approved local discovery workflows."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from site_agent.local_inventory import WindowsArpInventory, authorized_neighbors
from site_agent.models import DiscoveryTarget, ManagementProtocol
from site_agent.scope import AuthorizedScope
from site_agent.vendor_support import VendorFamily

from .controller import WindowsDiscoveryController
from .inventory_review import summarize_inventory
from .probe import ReadOnlyReachabilityProbe
from .vendor_support_view import contracts_for_display, protocol_allowed
from .workspace import WindowsWorkspace


class AutoNetWindowsApp:
    """Presents scope approval and read-only single-target discovery without storing passwords."""

    def __init__(self, root: tk.Tk, workspace_root: Path) -> None:
        """Build the local Windows application shell for a chosen workspace directory."""

        self._root = root
        self._controller = WindowsDiscoveryController(WindowsWorkspace(workspace_root), ReadOnlyReachabilityProbe().collect)
        self._site_id = tk.StringVar()
        self._networks = tk.StringVar()
        self._targets = tk.StringVar()
        self._approval_reference = tk.StringVar()
        self._address = tk.StringVar()
        self._protocol = tk.StringVar(value=ManagementProtocol.SSH.value)
        self._vendor_family = tk.StringVar(value=VendorFamily.CISCO.value)
        self._credential_reference = tk.StringVar()
        self._vendor_status = tk.StringVar()
        self._vendor_contracts = {contract.family.value: contract for contract in contracts_for_display()}
        self._acknowledged = tk.BooleanVar(value=False)
        self._status = tk.StringVar(value="Approve a read-only scope before discovery.")
        self._inventory: ttk.Treeview | None = None
        self._discovery_results = []
        self._build_view()

    def _build_view(self) -> None:
        """Render the small initial desktop surface using standard-library widgets only."""

        self._root.title("AutoNetArchitect — Local Discovery")
        self._root.minsize(760, 520)
        frame = ttk.Frame(self._root, padding=20)
        frame.grid(sticky="nsew")
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        fields = [
            ("Site identifier", self._site_id),
            ("Approved CIDR ranges (comma-separated)", self._networks),
            ("Explicit target addresses (comma-separated)", self._targets),
            ("Approval reference", self._approval_reference),
            ("Target management address", self._address),
            ("Credential reference only", self._credential_reference),
        ]
        ttk.Label(frame, text="Authorized local discovery", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(frame, text="This app never stores passwords and never uploads configuration from this screen.").grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 16))
        for row, (label, variable) in enumerate(fields, start=2):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=5)
            ttk.Entry(frame, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=5)
        protocol_row = len(fields) + 2
        ttk.Label(frame, text="Read-only protocol").grid(row=protocol_row, column=0, sticky="w", pady=5)
        protocol_box = ttk.Combobox(frame, textvariable=self._protocol, state="readonly", values=[item.value for item in ManagementProtocol])
        protocol_box.grid(row=protocol_row, column=1, sticky="ew", pady=5)
        vendor_row = protocol_row + 1
        ttk.Label(frame, text="Observed vendor family hint").grid(row=vendor_row, column=0, sticky="w", pady=5)
        vendor_box = ttk.Combobox(frame, textvariable=self._vendor_family, state="readonly", values=list(self._vendor_contracts))
        vendor_box.grid(row=vendor_row, column=1, sticky="ew", pady=5)
        vendor_box.bind("<<ComboboxSelected>>", lambda _event: self._update_vendor_status())
        ttk.Label(frame, textvariable=self._vendor_status, wraplength=680).grid(row=vendor_row + 1, column=0, columnspan=2, sticky="w", pady=(2, 6))
        self._update_vendor_status()
        ttk.Checkbutton(
            frame,
            text="I confirm this read-only scope and target list are authorized by the customer.",
            variable=self._acknowledged,
        ).grid(row=vendor_row + 2, column=0, columnspan=2, sticky="w", pady=(12, 4))
        ttk.Button(frame, text="Save approved scope", command=self._approve_scope).grid(row=vendor_row + 3, column=0, sticky="w", pady=(12, 4))
        ttk.Button(frame, text="Run read-only discovery", command=self._discover).grid(row=vendor_row + 3, column=1, sticky="e", pady=(12, 4))
        ttk.Button(frame, text="Review local ARP inventory", command=self._review_arp_inventory).grid(row=vendor_row + 4, column=0, sticky="w", pady=(8, 4))
        ttk.Button(frame, text="Review discovery evidence", command=self._review_discovery_evidence).grid(row=vendor_row + 4, column=1, sticky="e", pady=(8, 4))
        ttk.Label(frame, textvariable=self._status, wraplength=680).grid(row=vendor_row + 5, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self._inventory = ttk.Treeview(frame, columns=("address", "mac", "entry", "scope"), show="headings", height=7)
        for column, label, width in (
            ("address", "Address", 150),
            ("mac", "MAC evidence", 160),
            ("entry", "ARP entry", 120),
            ("scope", "Scope result", 160),
        ):
            self._inventory.heading(column, text=label)
            self._inventory.column(column, width=width, stretch=True)
        self._inventory.grid(row=vendor_row + 6, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        frame.rowconfigure(vendor_row + 6, weight=1)

    def _update_vendor_status(self) -> None:
        """Show the selected vendor contract and its evidence boundary without claiming support."""
        contract = self._vendor_contracts[self._vendor_family.get()]
        protocols = ", ".join(item.value for item in contract.protocols)
        self._vendor_status.set(
            f"{contract.family.value}: discovery protocols {protocols}. Configuration is blocked until exact platform, version, license, and path evidence are verified."
        )

    def _approve_scope(self) -> None:
        """Validate and save the local scope selected by the human operator."""

        try:
            networks = tuple(part.strip() for part in self._networks.get().split(",") if part.strip())
            targets = tuple(part.strip() for part in self._targets.get().split(",") if part.strip())
            scope = AuthorizedScope(
                site_id=self._site_id.get().strip(),
                approved_networks=networks,
                approved_targets=targets,
                allowed_protocols=(ManagementProtocol(self._protocol.get()),),
                approval_reference=self._approval_reference.get().strip(),
                operator_acknowledged=self._acknowledged.get(),
            )
            self._controller.approve_scope(scope)
            self._status.set("Read-only discovery scope saved locally. No device was contacted.")
        except ValueError as error:
            messagebox.showerror("Scope validation", str(error))

    def _discover(self) -> None:
        """Attempt a bounded read-only probe for one explicitly entered management endpoint."""

        try:
            contract = self._vendor_contracts[self._vendor_family.get()]
            protocol = ManagementProtocol(self._protocol.get())
            if not protocol_allowed(self._vendor_family.get(), protocol):
                raise PermissionError(f"{protocol.value} is not declared for the selected {contract.family.value} discovery contract.")
            target = DiscoveryTarget(
                address=self._address.get().strip(),
                protocol=protocol,
                credential_reference=self._credential_reference.get().strip(),
            )
            result = self._controller.discover_target(target)
            self._discovery_results.append(result)
            self._status.set(f"{result.state.value}: {result.message}")
        except (PermissionError, ValueError) as error:
            messagebox.showerror("Discovery blocked", str(error))

    def _review_arp_inventory(self) -> None:
        """Review local ARP cache entries only after scope approval, without probing any neighbor."""

        try:
            scope = self._controller.approved_scope()
            if scope is None:
                raise PermissionError("Save an approved local scope before reviewing local inventory.")
            neighbors = WindowsArpInventory().collect()
            targets = authorized_neighbors(scope, neighbors, ManagementProtocol(self._protocol.get()))
            authorized_addresses = {target.address for target in targets}
            if self._inventory is not None:
                for item in self._inventory.get_children():
                    self._inventory.delete(item)
                for neighbor in neighbors:
                    scope_result = "authorized candidate" if neighbor.address in authorized_addresses else "outside approved target scope"
                    self._inventory.insert("", tk.END, values=(neighbor.address, neighbor.mac_address, neighbor.entry_kind, scope_result))
            self._status.set(
                f"Local ARP cache contained {len(neighbors)} neighbor record(s); {len(targets)} matched the approved target and protocol scope."
            )
        except (PermissionError, RuntimeError, ValueError) as error:
            messagebox.showerror("Inventory review blocked", str(error))

    def _review_discovery_evidence(self) -> None:
        """Display recorded discovery outcomes without inventing facts for unresolved targets."""

        summary = summarize_inventory(self._discovery_results)
        review_window = tk.Toplevel(self._root)
        review_window.title("AutoNetArchitect — Discovery Evidence Review")
        review_window.minsize(780, 320)
        frame = ttk.Frame(review_window, padding=16)
        frame.grid(sticky="nsew")
        review_window.columnconfigure(0, weight=1)
        review_window.rowconfigure(0, weight=1)
        ttk.Label(
            frame,
            text=f"Recorded targets: {len(summary.rows)} · Unresolved: {summary.unresolved_count} · Abstained: {summary.abstained_count}",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))
        table = ttk.Treeview(frame, columns=("address", "state", "disposition", "facts", "evidence"), show="headings", height=10)
        for column, label, width in (("address", "Address", 130), ("state", "State", 110), ("disposition", "Disposition", 130), ("facts", "Observed facts", 210), ("evidence", "Evidence", 250)):
            table.heading(column, text=label)
            table.column(column, width=width, stretch=True)
        for row in summary.rows:
            facts = " · ".join(part for part in (row.vendor, row.platform, row.software_version) if part) or "No facts inferred"
            table.insert("", tk.END, values=(row.address, row.state.value, row.disposition.value, facts, row.evidence_message))
        table.grid(row=1, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)


def run() -> None:
    """Launch the Windows application using a secret-free local workspace under the user profile."""

    root = tk.Tk()
    workspace = Path.home() / "AutoNetArchitect"
    AutoNetWindowsApp(root, workspace)
    root.mainloop()


if __name__ == "__main__":
    run()
