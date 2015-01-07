<?php

/**
 * Product object.
 */
class Product
{
	/**
	 * Product code
	 * @var string
	 */
	public $Code;

	/**
	 * Quantity
	 * @var integer
	 */
	public $Quantity;

	/**
	 * Stores the code and quantity.
	 * The quantity will be cast to integer.
	 * 
	 * @param string
	 * @param integer
	 */
	public function __construct($ProductCode = "", $Quantity = 1)
	{
		$this->Code = $ProductCode;
		$this->Quantity = (int)$Quantity;
	}
}
