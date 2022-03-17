import mcqlib_GB100.mcqlib.main as main
import mcqlib_GB100.mcqlib.utils as utils

class GB100(main, utils):
    def __init__(self, name):
        pass

    def get_channel_balance(self):  # Gives channel that automatically changes
        super().get_channel_balance()

    def get_mainboard_total_flow(self):
        super().get_mainboard_total_flow()

    def get_channel_percent_value(self, channel):
        super().get_channel_percent_value(channel)

    def get_channel_id_gas(self, channel):  # Translate this to gas type
        super().get_channel_id_gas(channel)

    def get_channel_sccm(self, channel):  # Gives actual flow
        super().get_channel_sccm(channel)

    def get_channel_target_sccm(self, channel):  # Gives calculated flow
        super().get_channel_target_sccm(channel)

    def get_working_status(self):
        super().get_working_status()

    def get_channel_k_factor_gas(self, channel):
        super().get_channel_k_factor_gas(channel)

    def set_balance_channel(self, channel):
        super().set_balance_channel(channel)

    def set_mainboard_total_flow(self, flow):
        super().set_mainboard_total_flow(flow)

    def set_working_status_ON(self):
        super().set_working_status_ON()

    def set_working_status_OFF(self):
        super().set_working_status_OFF()

    def set_channel_id_gas_only(self, channel, gasID):
        super().set_channel_id_gas_only(channel, gasID)

    def set_channel_k_factor_only(self, channel, kfactor):
        super().set_channel_k_factor_only(channel, kfactor)

    def set_channel_enabled(self, channel):
        super().set_channel_enabled(channel)

    def set_channel_percent_value(self, channel, percent):
        super().set_channel_percent_value(channel, percent)

    def get_gas_type(self, gasID):  # Returns gas name from gas ID
        super().get_gas_type(gasID)
