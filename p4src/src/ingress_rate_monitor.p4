#include <core.p4>
#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef INGRESS_RATE_MONITOR
#define INGRESS_RATE_MONITOR
control ingress_rate_monitor(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    @name("flow_type_based_ingress_meter_for_upstream") meter(MAX_FLOW_TYPES,MeterType.packets) flow_type_based_ingress_meter;


    action monitor_incoming_flow_based_on_flow_type(bit<9> flow_type_based_meter_idx) {
        flow_type_based_ingress_meter.execute_meter((bit<32>)flow_type_based_meter_idx, local_metadata.rank_of_path_to_be_searched);
    }
    action monitor_incoming_flow_based_on_flow_type_without_param() {
            //flow_type_based_ingress_meter.execute_meter((bit<32>)flow_type_based_meter_idx, local_metadata.rank_of_path_to_be_searched);
            local_metadata.rank_of_path_to_be_searched = 0;
        }
    table flow_type_based_ingress_stats_table {
        key = {
            hdr.ipv6.traffic_class: exact ;
        }
        actions = {
            monitor_incoming_flow_based_on_flow_type;
            monitor_incoming_flow_based_on_flow_type_without_param;
        }
        default_action = monitor_incoming_flow_based_on_flow_type_without_param;
    }
    apply{
        flow_type_based_ingress_stats_table.apply();
    }

}

#endif


/*This ingress rate will measure a flows rate using a  meter and marke in one of the 3 color. This colors are indexed from 0 to 2
const bit<8> GREEN = 0x0;
const bit<8> YELLOW = 0x1;
const bit<8> RED = 0x2;

Now, if the ingress color is Green then we will use the 1-th best path, if color us Yellow we will sue k=2 th path
for Red we will use k=3 th path.

We will configure 3 ports  with rank 0,1,2.

so assume in real mptcp we have 3 streams or more than 3 streams. we can just mod with 3 to get a streamid number.

If a switch supports 8 paths we can say use 4 k=8 path in our system
*/