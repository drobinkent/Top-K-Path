
#include <core.p4>

#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef TOP_K_PATH_SELECTION
#define TOP_K_PATH_SELECTION
control top_k_path(inout parsed_headers_t    hdr,
                        inout local_metadata_t    local_metadata,
                        inout standard_metadata_t standard_metadata)
{
    table best_path_finder_mat {
        key = {
            local_metadata.best_path_selector_bitmask: ternary;
        }
        actions = {
            best_path_finder_action_without_param;
            best_path_finder_action_with_param;
        }
        default_action = best_path_finder_action_without_param;
    }

    action best_path_finder_action_without_param() {
        local_metadata.best_path_rank =0;
        //local_metadata.flag_hdr.found_multi_criteria_paths = false;
    }
    action best_path_finder_action_with_param(bit<32> rank) { //we do not neeeed this bcz our bitmask will lways give us a path
        local_metadata.best_path_rank = rank;
        //local_metadata.flag_hdr.found_multi_criteria_paths = true;
    }

    table worst_path_finder_mat {
        key = {
            local_metadata.worst_path_selector_bitmask: ternary;
        }
        actions = {//best_path_finder_action_without_param;
            worst_path_finder_action_with_param;
        }
        default_action = worst_path_finder_action_without_param;
    }

    action worst_path_finder_action_with_param(bit<32> rank) {
        local_metadata.worst_path_rank =rank;
        //local_metadata.flag_hdr.found_multi_criteria_paths = false;
    }
    action worst_path_finder_action_without_param() { //we do not neeeed this bcz our bitmask will lways give us a path
        local_metadata.worst_path_rank =0;
        //local_metadata.flag_hdr.found_multi_criteria_paths = true;
    }

    table kth_path_finder_mat {
        key = {
            local_metadata.kth_path_selector_bitmask: ternary;
        }
        actions = {//best_path_finder_action_without_param;
            kth_path_finder_action_with_param;
        }
        default_action = kth_path_finder_action_without_param;
    }

    action kth_path_finder_action_with_param(bit<32> rank) {
        local_metadata.kth_path_rank =rank;
        //local_metadata.flag_hdr.found_multi_criteria_paths = false;
    }
    action kth_path_finder_action_without_param() { //we do not neeeed this bcz our bitmask will lways give us a path
        local_metadata.kth_path_rank =0;
        local_metadata.flag_hdr.found_multi_criteria_paths = true;
    }


    apply {
         {

         }
    }
}
#endif










