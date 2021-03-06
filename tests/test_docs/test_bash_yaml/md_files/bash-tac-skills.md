``` bash
aea fetch fetchai/tac_controller:0.7.0
cd tac_controller
aea install
```
``` bash
aea create tac_controller
cd tac_controller
aea add connection fetchai/p2p_libp2p:0.7.0
aea add connection fetchai/soef:0.6.0
aea add connection fetchai/ledger:0.3.0
aea add skill fetchai/tac_control:0.5.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.7.0
aea config set agent.default_ledger cosmos
```
``` bash
aea fetch fetchai/tac_participant:0.8.0 --alias tac_participant_one
aea fetch fetchai/tac_participant:0.8.0 --alias tac_participant_two
cd tac_participant_two
aea install
```
``` bash
aea create tac_participant_one
aea create tac_participant_two
```
``` bash
cd tac_participant_one
aea add connection fetchai/p2p_libp2p:0.7.0
aea add connection fetchai/soef:0.6.0
aea add connection fetchai/ledger:0.3.0
aea add skill fetchai/tac_participation:0.6.0
aea add skill fetchai/tac_negotiation:0.7.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.7.0
aea config set agent.default_ledger cosmos
```
``` bash
cd tac_participant_two
aea add connection fetchai/p2p_libp2p:0.7.0
aea add connection fetchai/soef:0.6.0
aea add connection fetchai/ledger:0.3.0
aea add skill fetchai/tac_participation:0.6.0
aea add skill fetchai/tac_negotiation:0.7.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.7.0
aea config set agent.default_ledger cosmos
```
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
aea add-key cosmos cosmos_private_key.txt --connection
```
``` bash
aea config get vendor.fetchai.skills.tac_control.models.parameters.args.start_time
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.start_time '01 01 2020  00:01'
```
``` bash
aea run
```
``` bash
aea launch tac_controller tac_participant_one tac_participant_two
```
``` bash
aea delete tac_controller
aea delete tac_participant_one
aea delete tac_participant_two
```
``` yaml
default_routing:
  fetchai/oef_search:0.4.0: fetchai/soef:0.6.0
```
``` yaml
default_routing:
  fetchai/ledger_api:0.2.0: fetchai/ledger:0.3.0
  fetchai/oef_search:0.4.0: fetchai/soef:0.6.0
```
``` yaml
default_routing:
  fetchai/ledger_api:0.2.0: fetchai/ledger:0.3.0
  fetchai/oef_search:0.4.0: fetchai/soef:0.6.0
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
``` yaml
config:
  delegate_uri: 127.0.0.1:11002
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9002
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9002
```
