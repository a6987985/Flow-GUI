set ACTIVE_TARGETS = "init_design place_opt route_opt signoff"

set TARGET_LEVEL_init_design = "init"
set TARGET_LEVEL_place_opt = "place"
set TARGET_LEVEL_route_opt = "route"
set TARGET_LEVEL_signoff = "signoff"

set ALL_RELATED_place_opt = "init_design"
set ALL_RELATED_route_opt = "place_opt init_design"
set ALL_RELATED_signoff = "route_opt place_opt init_design"

set DEPENDENCY_OUT_init_design = "place_opt route_opt signoff"
set DEPENDENCY_OUT_place_opt = "route_opt signoff"
set DEPENDENCY_OUT_route_opt = "signoff"
set DEPENDENCY_OUT_signoff = "" 