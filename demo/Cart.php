<?php

/**
 * Shopping cart, main point of entry for the app.
 */
class Cart
{
	/**
	 * Total cost of products.
	 * @var integer
	 */
	public $Totals = 0;

	/**
	 * List of products
	 * @var Product[]
	 */
	public $Items;

	/**
	 * Sets an empty array for the Items
	 */
	public function __construct()
	{
		$this->Items = array();
	}

	/**
	 * Adds a Product item to the items array.
	 * Does not check if the product is already added, just appends them.
	 * Will trigger a refresh to recalculate the totals.
	 *
	 * <code>
	 * $cart = new Cart();
	 * $cart->addItem("MK", 3);
	 * </code>
	 * 
	 * @param string
	 * @param integer
	 */
	public function addItem($ProductCode = "", $Quantity = 1)
	{
		$this->Items[] = new Product($ProductCode, $Quantity);
		$this->refreshTotals();
	}

	/**
	 * Displays the contents of the Cart object.
	 * 
	 * @param  string $output output type
	 * @return null
	 */
	public function debug($output = "HTML")
	{
		$this->test();
		print_r($this);
	}

	/**
	 * Will refresh the total cart price.
	 * 
	 * @return null
	 */
	public function refreshTotals()
	{
		$this->Totals = 100 * count($this->Items);
	}
}
