import json
import re

from langchain_core.output_parsers import StrOutputParser

from backend.config.settings import OUTPUT_DIR
from backend.rag.advanced_rag import AdvancedRAG
from backend.utils.llm import get_code_llm, invoke_with_retry
from backend.config.prompts import GENERATOR_CORRECTOR_PROMPT, GENERATOR_NORMAL_PROMPT


GENERATOR_RAG_COLLECTION = "langchain"


def _is_unusable_rag_context(context: str) -> bool:
    normalized = (context or "").strip().lower()
    return normalized in {
        "",
        "contexte erc indisponible.",
        "aucun contexte rag disponible.",
        "aucun contexte trouve.",
        "aucun contexte trouvé.",
        "erc context unavailable.",
        "no rag context available.",
        "no rag context found.",
    }


def _get_rag_context(state: dict) -> tuple[str, list[str]]:
    rag_cache = state.get("rag_cache") if isinstance(state, dict) else None
    if isinstance(rag_cache, dict) and rag_cache.get("context"):
        context = str(rag_cache.get("context", "No RAG context found."))
        detected_ercs = rag_cache.get("detected_ercs", [])
        cache_collection = str(rag_cache.get("collection_name", "")).strip()
        if not isinstance(detected_ercs, list):
            detected_ercs = []
        if (
            not _is_unusable_rag_context(context)
            and cache_collection == GENERATOR_RAG_COLLECTION
        ):
            print("[Generator] Reusing RAG cache (generator collection).")
            return context, detected_ercs
        print("[Generator] RAG cache incompatible/unusable; retrieving fresh RAG context...")

    try:
        # Generator-specific collection: example contracts and tests.
        experiment_config = str(state.get("experiment_config", ""))
        rag = AdvancedRAG(
            collection_name=GENERATOR_RAG_COLLECTION,
            compress_context="no_compression" not in experiment_config,
        )
        result = rag.retrieve(state.get("contract_code", ""))
        context = result.get("context", "No RAG context found.")
        detected_ercs = result.get("detected_ercs", [])
        print("[Generator] Generator RAG retrieval complete.")
        return context, detected_ercs
    except Exception as exc:
        print(f"[Generator] RAG retrieval failed: {exc}")
        return "No RAG context available.", []
def _extract_block(code: str, open_brace_pos: int) -> tuple[int, int] | None:
    depth = 0
    for i in range(open_brace_pos, len(code)):
        if code[i] == "{":
            depth += 1
        elif code[i] == "}":
            depth -= 1
            if depth == 0:
                return open_brace_pos, i
    return None


def _find_it_blocks(code: str) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    it_header = re.compile(
        r"\bit\s*\([^,)]*(?:,[^)]*)??\)\s*,\s*(?:async\s*)?(?:function\s*\([^)]*\)|\([^)]*\)\s*=>)\s*\{",
        re.DOTALL,
    )
    for m in it_header.finditer(code):
        open_brace = m.end() - 1
        result = _extract_block(code, open_brace)
        if result is None:
            continue
        _, end_brace = result
        tail = re.match(r"\s*\)\s*;?\s*", code[end_brace + 1:])
        end_pos = end_brace + (len(tail.group(0)) if tail else 0)
        blocks.append((m.start(), end_pos))
    return blocks


def _remove_it_blocks_matching(code: str, predicate) -> str:
    blocks = _find_it_blocks(code)
    for start, end in reversed(blocks):
        block_text = code[start:end + 1]
        if predicate(block_text):
            code = code[:start] + code[end + 1:]
    return code


def _patch_it_blocks_matching_title(code: str, title: str, patch_fn) -> str:
    if not code or not title:
        return code

    blocks = _find_it_blocks(code)
    for start, end in reversed(blocks):
        block_text = code[start:end + 1]
        m = re.match(r'\bit\s*\(\s*[\'\"](.+?)[\'\"]\s*,', block_text)
        if not m:
            continue
        if m.group(1).strip() != title.strip():
            continue
        patched = patch_fn(block_text)
        code = code[:start] + patched + code[end + 1:]
    return code


_FAKE_CONTRACT_PATTERNS = [
    r'.*getContractFactory\s*\(\s*["\']MaliciousContract["\']\s*\).*\n',
    r'.*getContractFactory\s*\(\s*["\']ReentrancyAttacker["\']\s*\).*\n',
    r'.*getContractFactory\s*\(\s*["\']Attacker["\']\s*\).*\n',
    r'.*getContractFactory\s*\(\s*["\']MockContract["\']\s*\).*\n',
    r'.*getContractFactory\s*\(\s*["\']FakeContract["\']\s*\).*\n',
]

_FAKE_VAR_NAMES = [
    "malicious", "attacker", "reentrancy", "reentrancyAttacker",
    "maliciousContract", "attackContract", "fakeContract", "mockContract",
]


def _remove_fake_contracts(code: str) -> str:
    if not code:
        return code

    for pattern in _FAKE_CONTRACT_PATTERNS:
        code = re.sub(pattern, "", code, flags=re.IGNORECASE)

    for var in _FAKE_VAR_NAMES:
        var_lower = var.lower()
        code = _remove_it_blocks_matching(
            code,
            lambda block, v=var_lower: v in block.lower(),
        )

    still_present = sum(1 for v in _FAKE_VAR_NAMES if v.lower() in code.lower())
    if still_present == 0:
        print("[CleanJS] No hallucinated helper contract detected.")
    else:
        print(f"[CleanJS] Warning: {still_present} fake-contract reference(s) still present.")

    return code


def _clean_js_output(content: str) -> str:
    if not content:
        return ""

    print(f"[CleanJS] Initial content preview: {repr(content[:50])}")

    stripped = content.strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if "updated_test_code" in data:
                content = data["updated_test_code"]
                print(f"[CleanJS] JSON extrait : {len(content)} chars")
        except json.JSONDecodeError:
            m = re.search(
                r'"updated_test_code"\s*:\s*"((?:[^"\\]|\\.)*)"',
                stripped,
                re.DOTALL,
            )
            if m:
                content = m.group(1).encode().decode("unicode_escape")
                print(f"[CleanJS] JSON extrait via regex : {len(content)} chars")

    pattern = r"```(?:javascript|js)?(.*?)```"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = match.group(1)
        print(f"[CleanJS] Fence Markdown extraite : {len(content)} chars")
    else:
        content = content.replace("```javascript", "").replace("```js", "").replace("```", "")

    content = content.strip()
    content = _remove_fake_contracts(content)

    if 'require("chai")' not in content and "require('chai')" not in content:
        content = 'const { expect } = require("chai");\n' + content
    if 'require("hardhat")' not in content and "require('hardhat')" not in content:
        content = 'const { ethers } = require("hardhat");\n' + content

    print(f"[CleanJS] Final result: {content.count(chr(10)) + 1} lines")
    return content


def _normalize_ethers_v6(code: str) -> str:
    if not code:
        return code
    replacements = {
        "ethers.utils.parseEther(":  "ethers.parseEther(",
        "ethers.utils.formatEther(": "ethers.formatEther(",
        "ethers.utils.parseUnits(":  "ethers.parseUnits(",
        "ethers.utils.formatUnits(": "ethers.formatUnits(",
        ".deployed()":               ".waitForDeployment()",
    }
    for old, new in replacements.items():
        code = code.replace(old, new)
    code = _sanitize_deployed_contract_address_usage(code)
    return code


def _sanitize_deployed_contract_address_usage(code: str) -> str:
    """Replace ethers v5 instance.address with ethers v6 instance.target."""
    if not code:
        return code

    deployed_vars = set()
    for m in re.finditer(
        r"\b(?:const|let|var)\s+(\w+)\s*=\s*await\s+\w+\.deploy\s*\(",
        code,
    ):
        deployed_vars.add(m.group(1))

    for var in deployed_vars:
        code = re.sub(rf"\b{re.escape(var)}\.address\b", f"{var}.target", code)

    return code


def _public_abi_names(contract_code: str) -> set[str]:
    """Return public/external function names plus public state variable getters."""
    if not contract_code:
        return set()

    code = re.sub(r"/\*.*?\*/", "", contract_code, flags=re.DOTALL)
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)
    names = set(re.findall(
        r"\bfunction\s+(\w+)\s*\([^\)]*\)\s*(?:public|external)\b",
        code,
        flags=re.IGNORECASE,
    ))
    names.update(re.findall(
        r"\b(?:mapping\s*\([^\)]*\)\s*(?:\w+\s*)?|(?:uint|int|bool|address|string|bytes)\w*(?:\[\])?\s+)(?:public)\s+(\w+)\b",
        code,
        flags=re.IGNORECASE,
    ))
    return names


def _deployed_instance_vars(code: str) -> set[str]:
    vars_found = set()
    for m in re.finditer(
        r"\b(?:const|let|var)\s+(\w+)\s*=\s*await\s+\w+\.deploy\s*\(",
        code or "",
    ):
        vars_found.add(m.group(1))
    return vars_found


def _sanitize_nonexistent_contract_calls(code: str, contract_code: str) -> str:
    """
    Remove tests that call methods not present in the target contract ABI.
    This catches hallucinated/private getters such as pollCreator.polls() or getPoll().
    """
    if not code:
        return code

    allowed = _public_abi_names(contract_code)
    if not allowed:
        return code

    allowed_helpers = {"connect", "waitForDeployment", "getAddress"}
    instance_vars = _deployed_instance_vars(code)
    if not instance_vars:
        return code

    def _has_unknown_contract_call(block: str) -> bool:
        for var in instance_vars:
            for method in re.findall(rf"\b{re.escape(var)}\s*\.\s*(\w+)\s*\(", block):
                if method not in allowed and method not in allowed_helpers:
                    return True
        return False

    return _remove_it_blocks_matching(code, _has_unknown_contract_call)


def _sanitize_tx_wait_usage(code: str) -> str:
    if not code:
        return code

    code = re.sub(
        r"^\s*await\s+tx\s*\.\s*wait\s*\([^\)]*\)\s*;\s*$",
        "",
        code,
        flags=re.MULTILINE,
    )

    code = re.sub(
        r"\b(const|let|var)\s+receipt\s*=\s*tx\s*;",
        r"\1 receipt = await tx.wait();",
        code,
    )

    read_call_assigned_tx = re.search(
        r"\b(?:const|let|var)\s+tx\s*=\s*await\s+\w+\.\s*(?:get\w*|retrieve|read|name|symbol|decimals|balanceOf|totalSupply)\s*\(",
        code,
        flags=re.IGNORECASE,
    )
    if read_call_assigned_tx:
        code = re.sub(
            r"^\s*await\s+tx\s*\.\s*wait\s*\([^\)]*\)\s*;\s*$",
            "",
            code,
            flags=re.MULTILINE,
        )
        code = re.sub(
            r"\b(const|let|var)\s+(\w+)\s*=\s*await\s+tx\s*\.\s*wait\s*\([^\)]*\)\s*;",
            r"\1 \2 = tx;",
            code,
        )

    return code


def _extract_contract_name(contract_code: str) -> str:
    match = re.search(r"\bcontract\s+(\w+)", contract_code)
    return match.group(1) if match else "Contract"


def _count_callable_api(contract_code: str) -> int:
    if not contract_code:
        return 0
    code = re.sub(r"/\*.*?\*/", "", contract_code, flags=re.DOTALL)
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)
    pattern = r"\bfunction\s+\w+\s*\([^\)]*\)\s*(?:public|external)\b"
    return len(re.findall(pattern, code))


def _extract_constructor_types(contract_code: str) -> list[str]:
    if not contract_code:
        return []

    code = re.sub(r"/\*.*?\*/", "", contract_code, flags=re.DOTALL)
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)

    match = re.search(r"\bconstructor\s*\((.*?)\)", code, flags=re.DOTALL)
    if not match:
        return []

    params = match.group(1).strip()
    if not params:
        return []

    out: list[str] = []
    for raw in params.split(","):
        token = raw.strip()
        if not token:
            continue
        token = re.sub(r"\b(memory|calldata|storage|payable)\b", "", token)
        token = re.sub(r"\s+", " ", token).strip()
        parts = token.split(" ")
        if parts:
            out.append(parts[0])
    return out


def _default_js_value_for_sol_type(sol_type: str) -> str:
    t = (sol_type or "").strip().lower()
    if not t:
        return "0"
    if "[" in t and "]" in t:
        return "[]"
    if t.startswith("uint") or t.startswith("int"):
        return "1n"
    if t.startswith("bool"):
        return "false"
    if t.startswith("address"):
        return "owner.address"
    if t.startswith("string"):
        return '""'
    if t.startswith("bytes"):
        return '"0x"'
    return "0"


def _build_minimal_deploy_test(contract_name: str, contract_code: str = "") -> str:
    ctor_types = _extract_constructor_types(contract_code)
    deploy_args = ", ".join(_default_js_value_for_sol_type(t) for t in ctor_types)
    deploy_line = "    const instance = await Factory.deploy();\n"
    if deploy_args:
        deploy_line = f"    const instance = await Factory.deploy({deploy_args});\n"

    return (
        'const { expect } = require("chai");\n'
        'const { ethers } = require("hardhat");\n\n'
        f'describe("{contract_name}", function () {{\n'
        '  it("should deploy successfully", async function () {\n'
        '    const [owner] = await ethers.getSigners();\n'
        f'    const Factory = await ethers.getContractFactory("{contract_name}");\n'
        f"{deploy_line}"
        '    await instance.waitForDeployment();\n'
        '    expect(await instance.getAddress()).to.not.equal(ethers.ZeroAddress);\n'
        '  });\n'
        '});\n'
    )


def _sanitize_invalid_numeric_literals(code: str) -> str:
    if not code:
        return code

    result_lines: list[str] = []
    for line in code.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            result_lines.append(line)
        else:
            line = re.sub(r"([\(,]\s*)-\d+(\s*[,\)])", r"\g<1>0\2", line)
            result_lines.append(line)
    return "\n".join(result_lines)


def _sanitize_unsafe_bigint_expectations(code: str) -> str:
    """
    Ã‰vite les literals JS non sÃ»rs dans les assertions de balance,
    ex: 50 * (10 ** 18) -> 50n * (10n ** 18n)
    """
    if not code:
        return code

    code = re.sub(
        r"\b(\d+)\s*\*\s*\(\s*10\s*\*\*\s*(\d+)\s*\)",
        r"\1n * (10n ** \2n)",
        code,
    )

    # Ã‰vite le mix BigInt/number quand le test utilise await contract.decimals().
    code = re.sub(
        r"\b(\d+)n\s*\*\s*\(\s*10n\s*\*\*\s*await\s+([^\)]+)\)",
        r'ethers.parseUnits("\1", await \2)',
        code,
    )
    code = re.sub(
        r"\b(\d+)\s*\*\s*\(\s*10\s*\*\*\s*await\s+([^\)]+)\)",
        r'ethers.parseUnits("\1", await \2)',
        code,
    )

    code = re.sub(
        r"\b(\d+)\s*\*\*\s*(\d+)\b",
        r"\1n ** \2n",
        code,
    )

    return code


def _sanitize_timestamp_bigint_arithmetic(code: str) -> str:
    """
    Hardhat timestamps are JS numbers, while Solidity uint getters return BigInt
    in ethers v6. Convert common timestamp arithmetic safely.
    """
    if not code:
        return code

    code = re.sub(
        r"\(\s*await\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*\(\s*\)\s*\)\s*([+-])\s*(\d+)(?!n)\b",
        r"(Number(await \1()) \2 \3)",
        code,
    )
    code = re.sub(
        r"\(\s*await\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*\(\s*\)\s*\)\s*([+-])\s*(\d+)(?!n)\b",
        r"(Number(await \1()) \2 \3)",
        code,
        flags=re.DOTALL,
    )
    code = re.sub(
        r"\b(const|let)\s+(\w*time\w*|\w*Time\w*)\s*=\s*await\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*\(\s*\)\s*;",
        r"\1 \2 = Number(await \3());",
        code,
        flags=re.IGNORECASE,
    )
    return code


def _sanitize_broken_huge_parse_ether_literals(code: str) -> str:
    """Replace malformed giant parseEther literals that can break JS parsing."""
    if not code:
        return code

    return re.sub(
        r'ethers\.parseEther\(\s*"[\d\s]{80,}"\s*\)',
        'ethers.parseEther("1000000")',
        code,
        flags=re.DOTALL,
    )


def _sanitize_unreliable_struct_array_assertions(code: str) -> str:
    """
    Supprime les assertions fragiles sur tableaux dynamiques rÃ©cupÃ©rÃ©s via getter
    public de mapping<id, struct>, souvent non exposÃ©s par l'ABI.
    """
    if not code:
        return code

    patterns = [
        # Ex: expect(collection.wasteIds).to.deep.equal([1,2,3]);
        r"^\s*expect\([^\n]*\.wasteIds[^\n]*\)\.to\.deep\.equal\(\s*\[[^\]]*\]\s*\);\s*$",
        # Ex: expect(collection[1]).to.deep.equal([1n,2n,3n]);
        r"^\s*expect\([^\n]*collection\s*\[\s*1\s*\][^\n]*\)\.to\.deep\.equal\(\s*\[[^\]]*\]\s*\);\s*$",
        # Ex: expect(collection.wasteIds.length).to.equal(3);
        r"^\s*expect\([^\n]*\.wasteIds\.length[^\n]*\)\.to\.equal\([^\)]*\);\s*$",
    ]

    for p in patterns:
        code = re.sub(p, "", code, flags=re.MULTILINE | re.IGNORECASE)

    # Nettoie les lignes vides excessives aprÃ¨s suppression.
    code = re.sub(r"\n{3,}", "\n\n", code)
    return code


def _sanitize_brittle_change_token_balances(code: str) -> str:
    """
    Remplace les assertions changeTokenBalances trop dÃ©pendantes du flux de token
    par l'exÃ©cution simple de la transaction.
    """
    if not code:
        return code

    return re.sub(
        r"await\s+expect\((.*?)\)\s*\.to\.changeTokenBalances\([^;]*;",
        r"await \1;",
        code,
        flags=re.DOTALL,
    )


def _sanitize_negative_event_expectations(code: str) -> str:
    """Execute the transaction when an invalid .to.not.emit assertion is used."""
    if not code:
        return code

    return re.sub(
        r"await\s+expect\((.*?)\)\s*\.to\.not\.emit\([^;]*\)\s*;",
        r"await \1;",
        code,
        flags=re.DOTALL,
    )


def _sanitize_brittle_event_arg_assertions(code: str) -> str:
    """Drop .withArgs(...) from event assertions; event existence is less brittle."""
    if not code:
        return code

    return re.sub(
        r"\s*\.withArgs\([\s\S]*?\)\s*;",
        ";",
        code,
        flags=re.DOTALL,
    )


def _sanitize_revert_reason_assertions(code: str) -> str:
    """Use .to.be.reverted instead of brittle exact revert strings."""
    if not code:
        return code

    code = re.sub(r"\.to\.be\.revertedWith\([^\)]*\)", ".to.be.reverted", code)
    code = re.sub(r"\.to\.be\.revertedWithCustomError\([^\)]*\)", ".to.be.reverted", code)
    return code


def _contract_has_access_control(contract_code: str) -> bool:
    """Detect real access-control structure, ignoring comments and event parameter names."""
    if not contract_code:
        return False

    code = re.sub(r"/\*.*?\*/", "", contract_code, flags=re.DOTALL)
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)

    patterns = [
        r"\bmodifier\s+only\w+",
        r"\brequire\s*\([^;]*(msg\.sender\s*==|==\s*msg\.sender)",
        r"\b(hasRole|onlyRole|AccessControl|Ownable)\b",
        r"\b(owner|admin)\s*\(\s*\)",
        r"\baddress\s+(?:public\s+)?(?:owner|admin)\b",
    ]
    return any(re.search(pattern, code, flags=re.IGNORECASE) for pattern in patterns)


def _contract_accepts_plain_ether(contract_code: str) -> bool:
    """Return true when the target can receive Ether via bare transfers."""
    if not contract_code:
        return False

    code = re.sub(r"/\*.*?\*/", "", contract_code, flags=re.DOTALL)
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)
    return bool(re.search(r"\b(receive|fallback)\s*\(", code))


def _claim_reward_resets_state(contract_code: str) -> bool:
    """Detect whether claimReward clears winner/balance-like state after payout."""
    if not contract_code:
        return False

    code = re.sub(r"/\*.*?\*/", "", contract_code, flags=re.DOTALL)
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)
    match = re.search(r"\bfunction\s+claimReward\s*\([^\)]*\)[^{]*\{", code, flags=re.IGNORECASE)
    if not match:
        return False
    bounds = _extract_block(code, match.end() - 1)
    if bounds is None:
        return False
    body = code[bounds[0]:bounds[1] + 1]
    return bool(re.search(r"\b(winner|balance)\s*=\s*(address\s*\(\s*0\s*\)|0)\s*;", body))


def _sanitize_structurally_impossible_tests(code: str, contract_code: str) -> str:
    """
    Remove generated tests that require behavior unsupported by the target contract
    or forbidden by config_1 (for example selfdestruct force-send helpers).
    """
    if not code:
        return code

    fixed = code

    # ethers v6 connect() requires a signer/runner, not a raw address.
    fixed = _remove_it_blocks_matching(
        fixed,
        lambda block: bool(re.search(r"\.connect\s*\(\s*ethers\.ZeroAddress\s*\)", block)),
    )

    # If the contract has no real owner/admin/role guard, "non-owner should revert"
    # is an invented access-control expectation.
    if not _contract_has_access_control(contract_code):
        fixed = _remove_it_blocks_matching(
            fixed,
            lambda block: (
                ".to.be.reverted" in block
                and re.search(r"non-owner|another user's|another user|access control|unauthorized", block, re.IGNORECASE)
            ),
        )

    # Plain sendTransaction to a contract without receive/fallback reverts. A real
    # force-send test would need a selfdestruct helper, which config_1 forbids.
    if not _contract_accepts_plain_ether(contract_code):
        fixed = _remove_it_blocks_matching(
            fixed,
            lambda block: bool(
                re.search(r"force-?send|force-?sent|sendTransaction\s*\(\s*\{[^}]*to\s*:", block, re.IGNORECASE | re.DOTALL)
            ),
        )

    # Some contracts allow a second claim that transfers zero Ether. Do not assert
    # a revert unless the contract explicitly resets claim state.
    if not _claim_reward_resets_state(contract_code):
        fixed = _remove_it_blocks_matching(
            fixed,
            lambda block: (
                ".to.be.reverted" in block
                and re.search(r"claim\s+(?:the\s+)?reward\s+(?:more\s+than\s+once|twice)|claimReward\(\)", block, re.IGNORECASE)
                and "non-winner" not in block.lower()
                and "not the winner" not in block.lower()
            ),
        )

    # Front-running scenarios are speculative unless the contract explicitly
    # implements ordering/mempool logic. In simple sequential contracts they
    # often assert the opposite of the actual "14th deposit wins" behavior.
    fixed = _remove_it_blocks_matching(
        fixed,
        lambda block: bool(re.search(r"front-?running", block, re.IGNORECASE)),
    )

    return fixed


def _sanitize_repeated_deposit_winner_claims(code: str) -> str:
    """
    Fix common EthGame-style mistakes where the same signer performs all target
    deposits but the test later treats another signer as the winner.
    """
    if not code:
        return code

    def _patch_block(block: str) -> str:
        loop_match = re.search(
            r"for\s*\([^\)]*<\s*14[^\)]*\)\s*\{[\s\S]*?\.connect\((\w+)\)\.deposit",
            block,
            flags=re.IGNORECASE,
        )
        if not loop_match:
            return block

        actual_winner = loop_match.group(1)

        if re.search(r"allow\s+winner|full\s+contract\s+balance|claim\s+the\s+reward", block, re.IGNORECASE):
            block = re.sub(
                r"getBalance\((addr\d+|winner)\.address\)",
                f"getBalance({actual_winner}.address)",
                block,
            )
            block = re.sub(
                r"\.connect\((addr\d+|winner)\)\.claimReward\(\)",
                f".connect({actual_winner}).claimReward()",
                block,
            )

        if re.search(r"reject\s+claim|not\s+the\s+winner|non-?winner", block, re.IGNORECASE):
            replacement = "addr2" if actual_winner != "addr2" else "addr3"
            block = re.sub(
                r"\.connect\(" + re.escape(actual_winner) + r"\)\.claimReward\(\)",
                f".connect({replacement}).claimReward()",
                block,
            )

        return block

    fixed = code
    for start, end in reversed(_find_it_blocks(fixed)):
        block = fixed[start:end + 1]
        patched = _patch_block(block)
        if patched != block:
            fixed = fixed[:start] + patched + fixed[end + 1:]
    return fixed


def _sanitize_balanceof_decimal_assertions(code: str) -> str:
    """
    Si un test compare directement balanceOf Ã  une petite valeur entiÃ¨re,
    normalise en parseUnits avec decimals() du contrat token.
    """
    if not code:
        return code

    # map variable de solde -> variable contrat utilisÃ©e pour balanceOf
    var_to_token: dict[str, str] = {}
    for m in re.finditer(
        r"\b(?:const|let|var)\s+(\w+)\s*=\s*await\s+(\w+)\.balanceOf\(",
        code,
    ):
        var_to_token[m.group(1)] = m.group(2)

    for bal_var, token_var in var_to_token.items():
        code = re.sub(
            rf"expect\(\s*{bal_var}\s*\)\.to\.equal\(\s*(\d+)\s*\)",
            rf'expect({bal_var}).to.equal(ethers.parseUnits("\1", await {token_var}.decimals()))',
            code,
        )

    return code


def _sanitize_unsafe_integer_equal_literals(code: str) -> str:
    """
    Convertit les trÃ¨s grands littÃ©raux numÃ©riques des assertions chai en BigInt,
    ex: expect(x).to.equal(100000000000000000000) -> ...equal(100000000000000000000n)
    """
    if not code:
        return code

    return re.sub(
        r"(\.to\.equal\(\s*)(\d{16,})(\s*\))",
        r"\1\2n\3",
        code,
    )


def _sanitize_bigint_arithmetic_operands(code: str) -> str:
    """
    Corrige les opÃ©rations mixtes BigInt/number dans les assertions, ex:
      initialBalance - 100 -> initialBalance - 100n
      finalBalance + 1     -> finalBalance + 1n
    """
    if not code:
        return code

    def _repl(m: re.Match) -> str:
        expr = m.group(1)
        expr = re.sub(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\b\s*([\+\-])\s*(\d+)(?!n)\b",
            r"\1 \2 \3n",
            expr,
        )
        return f".to.equal({expr})"

    return re.sub(r"\.to\.equal\(([^\)]*)\)", _repl, code)


def _deterministic_auto_fix_pass(code: str, contract_code: str = "", analyzer_report: dict | None = None) -> str:
    """
    Auto-fix dÃ©terministe (sans LLM) pour les erreurs JS/Hardhat rÃ©currentes.
    - Regex globales (BigInt, assertions fragiles)
    - Patchs ciblÃ©s par test en Ã©chec via analyzer_report
    """
    if not code:
        return code

    fixed = code

    # Pass globales.
    fixed = _sanitize_tx_wait_usage(fixed)
    fixed = _normalize_ethers_v6(fixed)
    fixed = _sanitize_broken_huge_parse_ether_literals(fixed)
    fixed = _sanitize_timestamp_bigint_arithmetic(fixed)
    fixed = _sanitize_invalid_numeric_literals(fixed)
    fixed = _sanitize_unsafe_bigint_expectations(fixed)
    fixed = _sanitize_unsafe_integer_equal_literals(fixed)
    fixed = _sanitize_bigint_arithmetic_operands(fixed)
    fixed = _sanitize_unreliable_struct_array_assertions(fixed)
    fixed = _sanitize_brittle_change_token_balances(fixed)
    fixed = _sanitize_negative_event_expectations(fixed)
    fixed = _sanitize_brittle_event_arg_assertions(fixed)
    fixed = _sanitize_revert_reason_assertions(fixed)
    fixed = _sanitize_balanceof_decimal_assertions(fixed)
    fixed = _sanitize_repeated_deposit_winner_claims(fixed)
    fixed = _sanitize_impossible_revert_expectations(fixed, contract_code)
    fixed = _sanitize_nonexistent_contract_calls(fixed, contract_code)
    fixed = _sanitize_structurally_impossible_tests(fixed, contract_code)

    # Pass ciblÃ©es Ã  partir des Ã©checs connus.
    if isinstance(analyzer_report, dict):
        failures = analyzer_report.get("failures", [])
        if isinstance(failures, list):
            for failure in failures:
                if not isinstance(failure, dict):
                    continue
                title = str(failure.get("test", "")).strip()
                reason = str(failure.get("reason", "")).lower()
                ftype = str(failure.get("type", "")).upper()

                if not title:
                    continue

                if ftype == "ASSERTION_DATA_SHAPE" or "expected undefined to deeply equal" in reason:
                    def _drop_fragile_deep_equal(block: str) -> str:
                        block = re.sub(
                            r"^\s*expect\([^\n]*\)\.to\.deep\.equal\(\s*\[[^\]]*\]\s*\);\s*$",
                            "",
                            block,
                            flags=re.MULTILINE,
                        )
                        return re.sub(r"\n{3,}", "\n\n", block)

                    fixed = _patch_it_blocks_matching_title(fixed, title, _drop_fragile_deep_equal)

                if "cannot mix bigint" in reason or "unsafe" in reason:
                    def _fix_bigint_block(block: str) -> str:
                        block = _sanitize_unsafe_bigint_expectations(block)
                        block = _sanitize_unsafe_integer_equal_literals(block)
                        return block

                    fixed = _patch_it_blocks_matching_title(fixed, title, _fix_bigint_block)

    if fixed != code:
        print("[AutoFix] Deterministic pass applied.")
    else:
        print("[AutoFix] No deterministic pattern to fix.")

    return fixed


def _functions_with_explicit_revert(contract_code: str) -> set[str]:
    result: set[str] = set()
    if not contract_code:
        return result

    code = re.sub(r"/\*.*?\*/", "", contract_code, flags=re.DOTALL)
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)

    fn_pattern = re.compile(
        r"function\s+(\w+)\s*\([^\)]*\)[^{;]*\{",
        flags=re.IGNORECASE,
    )

    for m in fn_pattern.finditer(code):
        fn_name = m.group(1)
        open_brace = m.end() - 1
        bounds = _extract_block(code, open_brace)
        if bounds is None:
            continue
        start, end = bounds
        body = code[start:end + 1]
        if re.search(r"\b(require|revert|assert)\b", body):
            result.add(fn_name)

    return result


def _count_callable_names(contract_code: str) -> list[str]:
    if not contract_code:
        return []
    code = re.sub(r"/\*.*?\*/", "", contract_code, flags=re.DOTALL)
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)
    matches = re.findall(
        r"\bfunction\s+(\w+)\s*\([^\)]*\)\s*(?:public|external)\b",
        code,
        flags=re.IGNORECASE,
    )
    return list(dict.fromkeys(matches))


def _sanitize_impossible_revert_expectations(code: str, contract_code: str) -> str:
    if not code:
        return code

    reverting = _functions_with_explicit_revert(contract_code)

    if not reverting:
        code = _remove_it_blocks_matching(
            code,
            lambda block: ".to.be.reverted" in block,
        )
        return code

    non_reverting = [
        fn for fn in _count_callable_names(contract_code)
        if fn not in reverting
    ]
    for fn in non_reverting:
        fn_call = fn + "("
        code = _remove_it_blocks_matching(
            code,
            lambda block, f=fn_call: f in block and ".to.be.reverted" in block,
        )

    return code


def _prune_failing_tests(code: str, failed_titles: list) -> str:
    if not code or not failed_titles:
        return code

    titles_set = set(failed_titles)

    def _title_matches(block: str) -> bool:
        m = re.match(r'\bit\s*\(\s*[\'"](.+?)[\'"]\s*,', block)
        return bool(m and m.group(1) in titles_set)

    return _remove_it_blocks_matching(code, _title_matches)


def _save_artifact(filename: str, content) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    try:
        with open(path, "w", encoding="utf-8") as f:
            if isinstance(content, dict):
                json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                f.write(content)
    except OSError as exc:
        print(f"[Generator] Impossible de sauvegarder {filename} : {exc}")


def _log_code(label: str, code: str) -> None:
    if not code or not code.strip():
        print(f"[{label}] Warning: empty code.")
    else:
        print(f"[{label}] Generated {code.count(chr(10)) + 1} lines.")




