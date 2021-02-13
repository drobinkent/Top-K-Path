
#include <core.p4>

#include <v1model.p4>
#include "CONSTANTS.p4"
#include "headers.p4"
#include "parser.p4"


#ifndef TOP_K_PATH_SELECTION
#define TOP_K_PATH_SELECTION
control k_path_selector(inout parsed_headers_t    hdr,
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
        local_metadata.best_path_rank =INVALID_RANK;
    }
    action best_path_finder_action_with_param(bit<32> rank) {
        local_metadata.best_path_rank = rank;
    }

    table worst_path_finder_mat {
        key = {
            local_metadata.worst_path_selector_bitmask: ternary;
        }
        actions = {
            worst_path_finder_action_with_param;
            worst_path_finder_action_without_param;
        }
        default_action = worst_path_finder_action_without_param;
    }

    action worst_path_finder_action_with_param(bit<32> rank) {
        local_metadata.worst_path_rank =rank;
    }
    action worst_path_finder_action_without_param() { //we do not neeeed this bcz our bitmask will lways give us a path
        local_metadata.worst_path_rank =INVALID_RANK;
    }

    table kth_path_finder_mat {
        key = {
            local_metadata.kth_path_selector_bitmask: ternary;
        }
        actions = {
            kth_path_finder_action_without_param;
            kth_path_finder_action_with_param;
        }
        default_action = kth_path_finder_action_without_param;
    }

    action kth_path_finder_action_with_param(bit<32> rank) {
        local_metadata.kth_path_rank =rank;
    }
    action kth_path_finder_action_without_param() {
        local_metadata.kth_path_rank =INVALID_RANK;
    }


    apply {
         {
            bit<K> stored_bitmask_read_value = 0;
            stored_bitmask.read(stored_bitmask_read_value, (bit<32>)0);
            local_metadata.best_path_selector_bitmask = stored_bitmask_read_value;
            local_metadata.worst_path_selector_bitmask = stored_bitmask_read_value;
            bit<K> temp_mask = ALL_1_256_BIT[K-1:0] << local_metadata.rank_of_path_to_be_searched;
            local_metadata.kth_path_selector_bitmask = stored_bitmask_read_value & temp_mask ;

            best_path_finder_mat.apply();
            kth_path_finder_mat.apply();
            worst_path_finder_mat.apply();
         }
    }
}


#endif










