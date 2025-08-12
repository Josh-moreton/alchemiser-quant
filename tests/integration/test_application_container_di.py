
def test_create_for_testing_mocks_alpaca_manager(di_container):
    """The test container should supply a mocked AlpacaManager."""
    alpaca_manager = di_container.infrastructure.alpaca_manager()
    assert alpaca_manager.is_paper_trading
    account = alpaca_manager.get_account()
    assert account["account_id"] == "test_account"
