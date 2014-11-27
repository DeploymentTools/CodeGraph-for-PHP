<?php

class Cart
{
	public $Totals = 0;
	public $Items;

	public function __construct()
	{
		$this->Items = array();
	}

	public function addItem($ProductCode = "", $Quantity = 1)
	{
		$this->Items[] = new Product($ProductCode, $Quantity);
		$this->refreshTotals();
	}

	public function debug($output = "HTML")
	{
		$this->test();
		print_r($this);
	}

	public function refreshTotals()
	{
		$this->Totals = 100 * count($this->Items);
	}
}
