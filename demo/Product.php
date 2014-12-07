<?php

class Product
{
	public $Code;
	public $Quantity;

	public function __construct($ProductCode = "", $Quantity = 1)
	{
		$this->Code = $ProductCode;
		$this->Quantity = (int)$Quantity;
	}
}
