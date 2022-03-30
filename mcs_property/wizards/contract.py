from odoo import api, fields, models, _
from odoo.exceptions import UserError 
from odoo.exceptions import UserError

class ContractAddendum(models.TransientModel):
    _name = 'mcs_property.contract.addendum'
    _description = "Addendum Kontrak"

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.submit_addendum()

class ContractExpired(models.TransientModel):
    _name = 'mcs_property.contract.expired'
    _description = "Expired Kontrak"

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.submit_expired()

class ContractDone(models.TransientModel):
    _name = 'mcs_property.contract.done'
    _description = "Done Kontrak"

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.submit_done()

class ContractSuratPeringatan(models.TransientModel):
    _name = 'mcs_property.contract.surat_peringatan'
    _description = "Surat Peringatan Kontrak"

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.submit_surat_peringatan()

class ContractSuratPeringatanAlasan(models.TransientModel):
    _name = 'mcs_property.contract.surat_peringatan_alasan'
    _description = "Surat Peringatan Kontrak Alasan"

    wanprestasi_reason = fields.Html()
    wanprestasi_file = fields.Binary(string="Lampiran", attachment=True, track_visibility=True)
    wanprestasi_filename = fields.Char(string="Lampiran")

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.wanprestasi_reason = self.wanprestasi_reason
            contract.wanprestasi_file = self.wanprestasi_file
            contract.wanprestasi_filename = self.wanprestasi_filename
            contract.submit_surat_peringatan_alasan()

class ContractRunning(models.TransientModel):
    _name = 'mcs_property.contract.running'
    _description = "Running Kontrak"

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.submit_running()

class ContractApprove(models.TransientModel):
    _name = 'mcs_property.contract.approve'
    _description = "Approve Kontrak"

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.submit_approve() 

class ContractApproveDenied(models.TransientModel):
    _name = 'mcs_property.contract.approve.denied'
    _description = "Approve Kontrak"

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.deny_approve() 

class ContractConfirm(models.TransientModel):
    _name = 'mcs_property.contract.confirm'
    _description = "Konfirmasi Kontrak"

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.submit_confirm() 

class ContractExtend(models.TransientModel):
    _name = 'mcs_property.contract.extend'
    _description = "Perpanjangan Kontrak"

    start_date = fields.Date(track_visibility=True)
    end_date = fields.Date(track_visibility=True)

    def submit(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.new_start_date = self.start_date
            contract.new_end_date = self.end_date
            contract.submit_extend()

class ContractLostReason(models.TransientModel):
    _name = 'mcs_property.contract.lost.reason'
    _description = "Contract Lost Reason"

    lost_reason = fields.Many2one('mcs_property.lost_reason')
    lost_reason_detail = fields.Text()

    def submit_lost_reason(self): 
        context = dict(self._context)
        active_ids = context.get('active_ids', [])

        contracts = self.env['mcs_property.contract'].search([('id', 'in', active_ids)])

        count = len(contracts)
        if count <= 0:
            raise Warning("Data tidak ditemukan")
        for contract in contracts:
            contract.lost_reason = self.lost_reason
            contract.lost_reason_detail = self.lost_reason_detail
            contract.submit_cancel()