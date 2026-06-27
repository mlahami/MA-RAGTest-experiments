"""
prompts.py
----------
LangChain prompts used by the MA-RAGTest pipeline.

All LLM-facing instructions are intentionally written in English because:
- the paper and experiment tables are in English;
- generated tests, suites, and diagnostic reports should be directly usable in
  the paper;
- Solidity/Hardhat/Ethers examples are mostly documented in English.

Important: do not translate contract-specific revert strings. If a Solidity
contract reverts with a French string, generated tests must keep that exact
string when checking it.
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


_GLOBAL_RULES = """
You are an expert in Solidity, Hardhat, Mocha, Ethers.js v6, and smart-contract testing.

Absolute rules:
- Return the requested format only.
- Be deterministic and structured.
- Do not hallucinate functions, events, variables, contracts, getters, or constructor arguments.
- Always analyze the provided Solidity contract before designing or generating tests.
- Never rely on contract-specific hardcoded assumptions from examples.
- Preserve exact Solidity revert strings when the contract itself defines them.
"""


_COVERAGE_RULES = """
Coverage goals:
- Prioritize branch coverage for if/else, require, modifiers, and boolean paths.
- Include revert paths and boundary values.
- Cover all executable public/external behavior that can be tested without modifying the Solidity contract.
- Prefer meaningful assertions over superficial calls.
"""


_CODE_RULES = """
Critical JavaScript/Hardhat rules:

General:
- Use the exact target contract name from the provided Solidity code.
- Use ethers.getContractFactory("<ExactTargetContractName>") only for the target contract.
- Do not use hardcoded unrelated contract names from examples.
- Do not modify the Solidity contract.

Option A / config_1:
- Do not create or use helper, mock, receiver, attacker, or malicious contracts.
- Forbidden examples: MaliciousContract, ReentrancyAttacker, Attacker, MockReentrant,
  MockContract, FakeContract, MockERC20, MockERC721, MockFlashReceiver, FailingContract,
  NonPayableContract, ReentrantAttacker, ForceSend, ForceSender, SelfDestructSender.
- Do not write inline Solidity in the JavaScript test file.
- If a security scenario requires a helper/attacker/receiver contract, do not invent one.
  Replace it with an executable edge-case test on the target contract, or omit that test.

Solidity visibility and ABI:
- Test only public/external functions and public state-variable getters.
- Never call private/internal functions directly.
- Never call private mappings or hallucinated getters.
  Example: if the contract has `mapping(uint256 => Poll) private polls`,
  do not call `contract.polls(...)`; use public functions/events instead.
- If a generated test fails with "X is not a function", remove or rewrite that test using only real ABI members.

Ethers.js v6:
- Use ethers.parseEther() and ethers.parseUnits(), not ethers.utils.*.
- Use waitForDeployment(), not deployed().
- Use `contract.target` or `await contract.getAddress()`, not `contract.address`.
- Solidity uint/int return values are BigInt in Ethers v6.
- For BigInt arithmetic, use BigInt operands: 1n, 2n, BigInt(x).
- For Hardhat timestamp APIs such as evm_setNextBlockTimestamp, convert Solidity uint getters with Number(...):
  `Number(await contract.startTime()) + 3600`.
- Do not mix BigInt and JavaScript number values.

Transactions and fixtures:
- Use loadFixture from @nomicfoundation/hardhat-toolbox/network-helpers.
- Prefer signers from `await ethers.getSigners()`.
- Do not use ethers.Wallet.createRandom() unless you explicitly fund the wallet before any transaction.
- Do not call tx.wait() unless gas accounting is truly needed.
- For view/pure functions, never treat the return value as a transaction.

Assertions:
- Avoid brittle exact event-argument checks for timestamps, counters, trust scores, balances,
  gas-sensitive values, or values computed from block time.
- For such events, assert that the event was emitted, or check only stable arguments.
- Prefer `.to.be.reverted` over `.to.be.revertedWith("...")` unless the exact revert string
  is explicitly present in the Solidity contract and the setup guarantees that path.
- Do not expect a transaction to revert merely because a security best practice would prefer it.
  If the target contract intentionally allows the behavior, assert the actual behavior instead.
- Avoid fragile deep equality assertions on structs/tuples unless the ABI shape is certain.
- If a struct contains dynamic arrays through a mapping getter, do not assert unavailable fields by name.

Security feasibility:
- Do not generate "non-owner/non-admin should revert" tests unless the contract has a real owner/admin/role
  variable, modifier, or require(msg.sender == ...).
- Do not generate force-send/selfdestruct tests in config_1; they require helper contracts.
- Do not use contract.connect(ethers.ZeroAddress). Ethers connect() requires a signer, not an address.
- Do not assert that a second reward claim reverts unless the contract explicitly resets claim state.
- For "Nth deposit wins" contracts, the winner is the signer who performs the Nth deposit.
  If the same signer performs all deposits, that signer is the winner.
- Do not invent front-running scenarios unless the contract exposes ordering logic that can be tested
  with normal transactions.

Token/interface consumers:
- If the target contract only references token interfaces but does not implement them,
  treat it as a consumer, not as a token.
- In config_1, do not deploy external token mocks. Test only paths executable without helper contracts.
"""


_SECURITY_TAG_RULES = """
Security test tagging:
- The test strategy JSON contains `category` and `swc_id` fields.
- If category is "security", prefix the Mocha test title exactly as:
  it("[SECURITY:<swc_id_or_NA>] <should ...>", ...)
- Use "NA" when swc_id is null.
- Functional tests must not have a security tag.
- Preserve existing [SECURITY:...] tags when correcting tests.
- A security tag is a label, not proof of vulnerability detection. The test must still be executable.
"""


_SWC_APPLICABILITY_RULES = """
SWC applicability rules:
- Treat SWC context as candidate knowledge, not as mandatory tests.
- Assign a SWC ID only when the Solidity code contains a concrete structural pattern for that weakness.
- If the weakness is only a generic best practice and no executable behavior can be tested, make the test functional
  or set `swc_id` to null.
- Do not generate SWC-100 (Function Default Visibility) for Solidity versions where functions explicitly declare
  visibility or where the scenario cannot be observed through the ABI.
- Do not generate SWC-101 integer overflow/underflow tests for Solidity >=0.8.x unless the contract uses `unchecked`,
  inline assembly, or arithmetic whose wraparound behavior is explicitly reachable and observable.
- Do not generate SWC-105 access-control tests unless the contract contains an owner/admin/role variable, modifier,
  access-control require statement, or a documented privileged operation.
- Do not generate SWC-107 reentrancy tests unless the target function performs an external call, ETH transfer,
  token callback, or calls an untrusted contract before or around state updates.
- Do not generate SWC-114/front-running tests unless the contract exposes order-dependent behavior that can be tested
  deterministically with ordinary transactions.
- Do not generate SWC-120 randomness tests unless the contract uses block.timestamp, blockhash, block.number,
  block.prevrandao/difficulty, or similar chain attributes as randomness.
- Do not generate SWC-132 force-send/selfdestruct tests when helper/attacker contracts are forbidden; such tests require
  an external helper contract and must be omitted under config_1/config_2 Option A.
- Never expect a revert only because a vulnerability class says the behavior is risky. Expected reverts must be enforced
  by the Solidity code.
"""


TEST_DESIGNER_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        _GLOBAL_RULES + _SWC_APPLICABILITY_RULES + """
Goal: design a complete test strategy for the provided Solidity contract, covering
functional correctness and security-oriented scenarios.

Instructions:
- Identify the real public/external functions, modifiers, events, constructor parameters,
  state variables, and externally observable behavior.
- Design tests only for functions and getters available through the ABI.
- Ignore private/internal functions except through public/external callers.
- Use the SWC/security context to propose only structurally plausible security tests.
- Do not force a security test when the contract structure does not support an executable scenario.
- Prefer fewer high-confidence security tests over many generic SWC-labeled tests.
- In config_1, if a security scenario requires a helper/attacker/mock contract, mark the intended
  scenario as non-executable and omit it from executable test cases.

Return JSON only. It must be parseable by Python json.loads().

Required JSON schema:
{{
  "contract_name": "<exact contract name>",
  "test_suites": [
    {{
      "suite_name": "<suite name in English>",
      "test_cases": [
        {{
          "test_title": "<English should... title>",
          "target_function": "<public/external function or getter>",
          "inputs": {{}},
          "expected_behavior": "<English expected behavior; keep exact Solidity revert strings if needed>",
          "category": "functional|security",
          "swc_id": "<SWC-xxx or null>",
          "vulnerability_targeted": "<short description or null>"
        }}
      ]
    }}
  ]
}}
"""
    ),
    HumanMessagePromptTemplate.from_template("""
=== ERC / STANDARD CONTEXT ===
{erc_context}

=== SWC / SECURITY CONTEXT ===
{swc_context}

=== USER STORY / REQUIREMENTS ===
{user_story}

=== SOLIDITY CONTRACT ===
{contract_code}
"""),
])


GENERATOR_NORMAL_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        _GLOBAL_RULES + _COVERAGE_RULES + _CODE_RULES + _SECURITY_TAG_RULES + _SWC_APPLICABILITY_RULES + """
Goal: generate a complete Hardhat/Mocha JavaScript test file from the provided strategy.

Before writing code:
1. Extract the exact target contract name from the Solidity code.
2. List the ABI-callable public/external functions and public getters.
3. Use only those ABI-callable members.
4. Keep generated suite names, test titles, and comments in English.
5. Preserve exact revert strings from the contract when asserting them.
6. Re-check every security/SWC test against the Solidity code; remove or downgrade tests whose SWC label is not
   structurally supported by executable contract behavior.

Output format:
- Return raw JavaScript code only.
- Do not return Markdown fences.
- Do not return JSON.
- Start directly with:
const {{ expect }} = require("chai");
"""
    ),
    HumanMessagePromptTemplate.from_template("""
=== 1. ERC / STANDARD CONTEXT ===
{erc_context}

=== 2. EXAMPLES AND BEST PRACTICES ===
{relevant_examples}

=== 3. SOLIDITY CONTRACT ===
{contract_code}

=== 4. TEST STRATEGY JSON ===
{test_design_json}
"""),
])


GENERATOR_CORRECTOR_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        _GLOBAL_RULES + _COVERAGE_RULES + _CODE_RULES + _SECURITY_TAG_RULES + _SWC_APPLICABILITY_RULES + """
Goal: correct or extend the existing JavaScript tests according to correction_mode.

correction_mode:
- fix_failing_tests: prioritize fixing failing tests.
- improve_coverage: all tests pass, but coverage is insufficient.
- general_refinement: keep the suite stable unless a small correction is necessary.

Priority rules:
- Do not rewrite the whole suite when only a few tests need changes.
- Preserve passing tests.
- Do not modify the Solidity contract.
- Return a complete, compilable Hardhat test file.
- Keep generated suite names, test titles, and comments in English.

When fixing failures:
- If "X is not a function", remove or rewrite the test using only real ABI members.
- If a private/internal getter or mapping is being called, remove that call and test through public behavior.
- If BigInt/number mixing occurs, convert timestamps with Number(...) or use BigInt operands consistently.
- If a revert reason differs, prefer `.to.be.reverted` unless the exact string is guaranteed by the contract.
- If an event argument is dynamic or time-dependent, assert event emission only or check stable arguments.
- If a helper/attacker/mock contract is required, do not create it in config_1; remove or replace that test.
- If a test claims to be security-oriented but does not test executable behavior, make it functional or remove the security tag.
- If a failing SWC-labeled test expects behavior not enforced by the Solidity code, remove that test or convert it into
  an assertion of the actual observable behavior.

Output format:
- Return raw JavaScript code only.
- No Markdown fences.
- No JSON wrapper.
- Start directly with:
const {{ expect }} = require("chai");
"""
    ),
    HumanMessagePromptTemplate.from_template("""
=== 1. CORRECTION MODE ===
{correction_mode}

=== 2. ERC / STANDARD CONTEXT ===
{erc_context}

=== 3. EXAMPLES AND BEST PRACTICES ===
{relevant_examples}

=== 4. SOLIDITY CONTRACT ===
{contract_code}

=== 5. CURRENT TEST CODE ===
{test_code}

=== 6. FAILING TESTS EXTRACTED BY ANALYZER ===
{failed_tests_json}

=== 7. ANALYZER REPORT ===
{analyzer_json}

=== 8. HARDHAT EXECUTION SUMMARY ===
{execution_summary_json}

=== 9. TARGET CONTRACT COVERAGE SUMMARY ===
{coverage_summary_json}

=== 10. HARDHAT STDOUT ===
{test_stdout}

=== 11. HARDHAT STDERR ===
{test_stderr}
"""),
])


ANALYZER_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        _GLOBAL_RULES + _COVERAGE_RULES + """
Goal: analyze generated tests and report failures, missing coverage, and missing edge cases.

Return JSON only:
{{
  "failures": [
    {{
      "test": "<test name>",
      "reason": "<why it failed>",
      "type": "CALL_ERROR|REVERT_MISMATCH|ASSERTION_MISMATCH|ASSERTION_DATA_SHAPE|UNDEFINED_HELPER_CONTRACT|INVALID_JS_SYNTAX|BIGINT_MIX|OTHER",
      "fix": "<English correction guidance; never suggest modifying the Solidity contract>"
    }}
  ],
  "missing_coverage": {{
    "functions": [],
    "branches": [],
    "edge_cases": []
  }},
  "suggestions": []
}}
"""
    ),
    HumanMessagePromptTemplate.from_template("""
Contract:
{contract_code}

Test code:
{test_code}

Test report:
{mochawesome_json}

Coverage:
{coverage_json}
"""),
])


EVALUATOR_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        _GLOBAL_RULES + """
Goal: decide whether the pipeline should stop or regenerate tests.

Return JSON only:
{{ "decision": "stop|regenerate", "reason": "<clear English reason>" }}

Regenerate when:
- correctable tests still fail;
- statement coverage is below 85%;
- branch coverage is below 80% when the target contract has instrumented branches.

Stop when:
- all tests pass and applicable coverage thresholds are satisfied;
- all remaining failures are structurally non-correctable under config_1;
- the pipeline is rate-limited;
- repeated iterations stagnate.
"""
    ),
    HumanMessagePromptTemplate.from_template("""
Execution summary:
{execution_summary}

Analyzer report:
{analyzer_json}
"""),
])
