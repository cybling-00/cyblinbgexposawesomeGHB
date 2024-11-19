<template>
  <div fluid>
    <v-row>
      <v-col md="12" cols="12" class="pb-1 pr-0">
        <v-card class="main mx-auto grey lighten-5 mt-3 p-3 pb-16 overflow-y-auto"
          style="max-height: 94vh; height: 94vh">
          <v-select dense outlined clearable background-color="white" :items="cash_transit_list" label="Transit Type"
            v-model="fields.transit_type" @change="transit_type_change"></v-select>
          <v-divider></v-divider>
          <v-row v-show="this.fields.transit_type" no-gutters class="p-1 m-2">
            <v-col cols="5" class="p-1">
              <v-select dense outlined clearable background-color="white" :items="bank_chart_of_account_list"
                label="Bank Account" v-model="fields.bank_account"></v-select>
            </v-col>
            <v-col cols="5" class="p-1">
              <v-text-field dense outlined clearable color="primary" label="Amount" background-color="white"
                :rules="[isNumber]" v-model="fields.amount"></v-text-field>
            </v-col>
            <v-col cols="2" class="p-1">
              <v-btn block color="primary" dark @click="submit">
                {{ __("Submit") }}
              </v-btn>
            </v-col>

          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>

import { evntBus } from "../../bus";
import format from "../../format";

export default {
  mixins: [format],
  data: function () {
    return {
      pos_profile: "",
      company: "",
      cash_transit_list: ["Widthdrawal", "Deposit"],
      bank_chart_of_account_list: [],
      cash_account: "",
      fields: {
        "transit_type": "",
        "bank_account": "",
        "amount": 0
      }

    };
  },
  methods: {
    show_error(msg) {
      evntBus.$emit("show_mesage", {
          text: __(msg),
          color: "error",
        });
    },
    clear_all(transit_type = true) {
      if(transit_type){
        this.fields.transit_type = ''
      }
      this.fields.bank_account = ''
      this.fields.amount = 0
    },
    get_chart_of_account() {
      return frappe
        .call("posawesome.posawesome.api.posapp_custom.get_cash_transit_data", {
          user: frappe.session.user
        })
        .then((r) => {
          if (r.message) {
            let data = r.message;
            this.pos_profile = data.pos_profile;
            this.company = data.company;
            this.cash_account = data.cash_account;
            this.bank_chart_of_account_list = data.bank_chart_of_account;
          }
        });
    },
    transit_type_change() {
      this.clear_all(false)
    },
    submit() {
      let vm = this
      if (!vm.fields.transit_type) {
        vm.show_error(`Please select a Transit Type !`)
        return;
      }
      if (!vm.cash_account) {
        vm.show_error(`Please select a Bank Account !`)
        return;
      }
      if (!vm.fields.bank_account) {
        vm.show_error(`Please select a Bank Account !`)
        return;
      }
      if (flt(vm.fields.amount) <= 0) {
        vm.show_error(`Please select Valid Amount !`)
        return;
      }
      const payload = {};
      payload.company = vm.company.name;
      payload.pos_profile = vm.pos_profile.name;
      payload.cash_account = vm.cash_account;
      payload.transit_type = vm.fields.transit_type;
      payload.bank_account = vm.fields.bank_account;
      payload.amount = vm.fields.amount;
      frappe.call({
        method: "posawesome.posawesome.api.posapp_custom.make_transit_type_journal_entry",
        args: { data: payload },
        freeze: true,
        freeze_message: __("Making Entry !"),
        callback: function (r) {
          if (r.message) {
            evntBus.$emit("show_mesage", {
              text: __(`Entry ${r.message} is Submitted !`),
              color: "success",
            });
          }
          vm.clear_all()
        },
      });
    },
  },

  computed: {

  },
  mounted: function () {
    this.$nextTick(function () {
      this.get_chart_of_account();
    });
  },
};
</script>

<style></style>
